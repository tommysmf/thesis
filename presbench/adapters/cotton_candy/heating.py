"""Heating model of the cotton candy head, to simulate the head temperature after a start that did not happen.

A single decision can replay the real signal (see README.md), but a start and a stop together cannot: after a
counterfactual start the head spins while the real run was still waiting, or the other way round. This module
models each phase of a real run, chosen by forecasting held-out readings (validate_heating.py, heating_report.md):

  WAITING (machine on until the real start): a straight line, the run's own slope (the Newton curve's ceiling
          hits its bound for almost every run, and the line forecasts better); runs with too few waiting
          readings use the median slope of their batch.
  SPINNING (real start until the real stop): Newton's law of heating, dT/dt = k * (T_inf - T), i.e.
          T(tau) = T_inf - (T_inf - T_anchor) * exp(-k * tau), with T_inf and k pooled over the run's batch
          (all runs if the batch has too few readings). The pooled curve forecasts better than the run's own.

The real deviations from the fit (residuals) are added back, indexed by time since the phase started and
repeated when the simulation runs longer than the real phase, so the simulated signal keeps the real noise.

    h = fit_heating(cases)                      # per case_id: HeatingFit
    T = trajectory(case, h[case.case_id], s)    # head at case.times for a start at s (s since t0)

Real readings are used wherever the real run was in the same state as the simulated one: before the earlier of
the real and the simulated start, and during the real spinning phase when s equals the real start.
"""
from dataclasses import dataclass, field
import numpy as np
from scipy.optimize import curve_fit

MIN_READINGS, MIN_SPAN, MIN_R2 = 8, 15.0, 0.8   # a phase fit is used for its run only above these
T_INF_MAX = 160.0                               # C: upper bound of the fitted ceiling (keeps extrapolation sane)
K_MIN = 1e-3                                    # 1/s: lower bound of the Newton rate (avoids a flat, degenerate fit)
START_TOL = 1e-6                                # s: a start this close to the real start counts as the real one


def newton(tau, t_inf, k, t_anchor):
    return t_inf - (t_inf - t_anchor) * np.exp(-k * np.asarray(tau, dtype=float))


@dataclass
class PhaseFit:
    kind: str                                    # "line" (constant rate `slope`) or "newton" (t_inf, k)
    source: str                                  # parameters from the "run", its "batch" or "all" runs
    slope: float = np.nan                        # C/s, for kind "line"
    t_inf: float = np.nan                        # C, for kind "newton"
    k: float = np.nan                            # 1/s, for kind "newton"
    r2: float = np.nan                           # in-sample fit on the run's own phase
    rmse: float = np.nan
    res_tau: np.ndarray = field(default_factory=lambda: np.array([0.0]))   # residuals of the run's own phase,
    res: np.ndarray = field(default_factory=lambda: np.array([0.0]))       # by time since the phase started

    def curve(self, tau, t_anchor):
        tau = np.asarray(tau, dtype=float)
        if self.kind == "line":
            return t_anchor + self.slope * tau
        return newton(tau, self.t_inf, self.k, t_anchor)

    def rate(self, temp):
        return self.slope if self.kind == "line" else self.k * (self.t_inf - temp)

    def residual(self, tau):
        """Real residual at time tau since the phase started; repeated beyond the real phase length."""
        tau = np.asarray(tau, dtype=float)
        span = self.res_tau[-1] if len(self.res_tau) > 1 else 0.0
        if span <= 0:
            return np.zeros_like(tau)
        return np.interp(np.mod(tau, span), self.res_tau, self.res)

    def path(self, tau, t_anchor, noise=True):
        """Head at tau s after the phase started at t_anchor: the curve plus the real residuals, continuous at 0."""
        if not noise:
            return self.curve(tau, t_anchor)
        r0 = float(self.residual(0.0))
        return self.curve(tau, t_anchor - r0) + self.residual(tau)


@dataclass
class HeatingFit:
    wait: PhaseFit
    spin: PhaseFit


def fit_phase(x, y):
    """Least-squares Newton fit of readings y at times x (x[0] = 0). Returns (t_inf, k, t0, r2, rmse) or None."""
    if len(x) < 3:
        return None
    try:
        p, _ = curve_fit(newton, x, y, p0=[min(110.0, T_INF_MAX), 0.01, y[0]],
                         bounds=([y.max(), 1e-4, 0.0], [T_INF_MAX, 0.2, 150.0]), maxfev=5000)
    except (RuntimeError, ValueError):
        return None
    fit = newton(x, *p)
    ss = np.sum((y - y.mean()) ** 2)
    r2 = 1 - np.sum((y - fit) ** 2) / ss if ss > 0 else np.nan
    return p[0], p[1], p[2], r2, float(np.sqrt(np.mean((y - fit) ** 2)))


def phase_readings(case, phase):
    """Times since the phase started and head readings of the real run in that phase."""
    a, b = case.info["t_real_start"], case.info["t_real_end"]
    lo, hi = (0.0, a) if phase == "wait" else (a, b)
    m = (case.times >= lo) & (case.times <= hi)
    return case.times[m] - lo, case.signal[m]


def _pooled(cases, phase):
    """One Newton curve (shared T_inf and k) through the readings of several runs, each run with its own starting
    level: a joint least-squares fit on the temperatures themselves. Returns (T_inf, k) or None."""
    data = [phase_readings(c, phase) for c in cases]
    data = [(x, y) for x, y in data if len(x) >= 3]
    if not data:
        return None
    xs = np.concatenate([x for x, _ in data])
    ys = np.concatenate([y for _, y in data])
    run = np.concatenate([np.full(len(x), i) for i, (x, _) in enumerate(data)])

    def model(_, t_inf, k, *t0):
        return newton(xs, t_inf, k, np.asarray(t0)[run])

    p0 = [min(110.0, T_INF_MAX), 0.01] + [y[0] for _, y in data]
    lo = [ys.max(), K_MIN] + [0.0] * len(data)
    hi = [T_INF_MAX, 0.2] + [150.0] * len(data)
    p0[0] = float(np.clip(p0[0], lo[0] + 1e-6, hi[0]))
    try:
        p, _ = curve_fit(model, xs, ys, p0=p0, bounds=(lo, hi), maxfev=20000)
    except (RuntimeError, ValueError):
        return None
    return float(p[0]), float(p[1])


def fit_line(x, y):
    """Least-squares line through readings y at times x. Returns (slope, intercept, r2, rmse)."""
    slope, intercept = np.polyfit(x, y, 1)
    fit = intercept + slope * x
    ss = np.sum((y - y.mean()) ** 2)
    return slope, intercept, (1 - np.sum((y - fit) ** 2) / ss if ss > 0 else np.nan), \
        float(np.sqrt(np.mean((y - fit) ** 2)))


def _own_line(case):
    x, y = phase_readings(case, "wait")
    if len(x) < MIN_READINGS or x[-1] - x[0] < MIN_SPAN:
        return None
    line = fit_line(x, y)
    return line if line[2] >= MIN_R2 else None


def batch_slope(cases):
    """Median own waiting slope of the runs passed (None if none has a usable own line)."""
    s = [line[0] for line in map(_own_line, cases) if line is not None]
    return float(np.median(s)) if s else None


def fit_heating(cases):
    """HeatingFit per case_id. Waiting: the run's own line, else its batch's median slope, else all runs'.
    Spinning: the Newton curve pooled over the run's batch, else over all runs."""
    groups = sorted({c.group for c in cases})
    slopes = {g: batch_slope([c for c in cases if c.group == g]) for g in groups}
    slopes["all"] = batch_slope(cases)
    spins = {g: _pooled([c for c in cases if c.group == g], "spin") for g in groups}
    for g in groups:                                 # a fit stuck at the lower rate bound is flat: use all runs
        if spins[g] is not None and spins[g][1] <= K_MIN * 1.01:
            spins[g] = None
    spins["all"] = _pooled(cases, "spin")
    fits = {}
    for c in cases:
        x, y = phase_readings(c, "wait")
        own = _own_line(c)
        if own is not None:
            wait = PhaseFit("line", "run", slope=own[0], r2=own[2], rmse=own[3])
            wait.res_tau, wait.res = x, y - (own[1] + own[0] * x)
        else:
            src = c.group if slopes[c.group] is not None else "all"
            wait = PhaseFit("line", "batch" if src == c.group else "all", slope=slopes[src])
            if len(x) >= 3:
                wait.res_tau, wait.res = x, y - (y[0] + wait.slope * x)
        x, y = phase_readings(c, "spin")
        src = c.group if spins[c.group] is not None else "all"
        t_inf, k = spins[src]
        spin = PhaseFit("newton", "batch" if src == c.group else "all", t_inf=t_inf, k=k)
        if len(x) >= 3:                                  # residuals around the pooled curve, from the first reading
            fit = newton(x, t_inf, k, y[0])
            spin.res_tau, spin.res = x, y - fit
            ss = np.sum((y - y.mean()) ** 2)
            spin.r2 = 1 - np.sum((y - fit) ** 2) / ss if ss > 0 else np.nan
            spin.rmse = float(np.sqrt(np.mean((y - fit) ** 2)))
        fits[c.case_id] = HeatingFit(wait, spin)
    return fits


def trajectory(case, fit, start, noise=True):
    """Head temperature at case.times if spinning had started at `start` (s since t0) and continued.

    t <= min(start, real start): the real readings (the run was waiting in both worlds).
    start > real start: from the real start to `start` the head keeps WAITING (wait model, from the real head at
    the real start); after `start` it SPINS (spin model, from the head at `start`).
    start == real start: the real readings up to the real stop, the spin model after it.
    """
    a, b = case.info["t_real_start"], case.info["t_real_end"]
    t = case.times
    out = case.signal.astype(float).copy()
    if abs(start - a) <= START_TOL:
        after = t > b
        if after.any():
            out[after] = fit.spin.path(t[after] - a, case.signal_at(a), noise)
            out[after] += case.signal_at(b) - fit.spin.path(b - a, case.signal_at(a), noise)   # continuous at b
        return out
    head_start = case.signal_at(start)
    if start > a:
        w = (t > a) & (t <= start)
        out[w] = _wait_from(fit, case, t[w], noise)
        head_start = float(_wait_from(fit, case, np.array([start]), noise)[0])
    s = t > start
    out[s] = fit.spin.path(t[s] - start, head_start, noise)
    return out


def _wait_from(fit, case, t, noise):
    """Waiting continued after the real start: the wait model from the real head at the real start, with the
    run's waiting residuals continued in time since machine on."""
    a = case.info["t_real_start"]
    curve = fit.wait.curve(t - a, case.signal_at(a))
    if not noise:
        return curve
    return curve + fit.wait.residual(t) - fit.wait.residual(a)
