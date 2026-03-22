'use client';

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:4000';
const REQUEST_TIMEOUT_MS = 12000;
const MAX_RETRIES = 2;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT_MS,
  headers: { 'Content-Type': 'application/json' },
});

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Slider config
// These 6 keys map to the /api/run-simulation endpoint payload.
// They also map to the 7 existing policy keys when richer baseForecast data is
// available (charging_infrastructure -> charging_infra, etc.).
const SLIDER_CONFIG = [
  {
    key: 'charging_infra',
    label: 'Charging Infrastructure',
    description: 'Public charging network expansion (weight: 30%)',
    min: 0, max: 100, default: 50, weight: 0.30,
    policyKey: 'charging_infrastructure',
  },
  {
    key: 'subsidies',
    label: 'Consumer Subsidies (FAME II)',
    description: 'Direct purchase incentives for EV buyers (weight: 25%)',
    min: 0, max: 100, default: 50, weight: 0.25,
    policyKey: 'consumer_subsidies',
  },
  {
    key: 'manufacturing',
    label: 'Manufacturing Incentives (PLI)',
    description: 'Subsidies for local EV manufacturing (weight: 20%)',
    min: 0, max: 100, default: 50, weight: 0.20,
    policyKey: 'manufacturing_incentives',
  },
  {
    key: 'rnd',
    label: 'R&D and Battery Technology',
    description: 'Battery technology and innovation funding (weight: 10%)',
    min: 0, max: 100, default: 50, weight: 0.10,
    policyKey: 'rd_investment',
  },
  {
    key: 'mandates',
    label: 'EV Regulatory Mandates',
    description: 'Mandatory EV sales targets for OEMs (weight: 10%)',
    min: 0, max: 100, default: 50, weight: 0.10,
    policyKey: 'regulatory_mandates',
  },
  {
    key: 'state_incentives',
    label: 'State-Level Incentives',
    description: 'Regional tax benefits and subsidies (weight: 5%)',
    min: 0, max: 100, default: 50, weight: 0.05,
    policyKey: 'state_policies',
  },
];

// Presets
const PRESETS = {
  china_model: {
    name: 'China Success Model',
    description: "Based on China's EV transition (2015-2020)",
    values: { charging_infra: 75, subsidies: 90, manufacturing: 100, rnd: 66, mandates: 80, state_incentives: 53 },
  },
  aggressive_growth: {
    name: 'Aggressive Growth',
    description: 'Maximum incentives for rapid market penetration',
    values: { charging_infra: 90, subsidies: 88, manufacturing: 100, rnd: 80, mandates: 100, state_incentives: 80 },
  },
  balanced: {
    name: 'Balanced Approach',
    description: 'Moderate incentives across all policy areas',
    values: { charging_infra: 60, subsidies: 60, manufacturing: 60, rnd: 66, mandates: 66, state_incentives: 66 },
  },
  current_india: {
    name: 'Current India (BAU)',
    description: 'Approximate current policy levels',
    values: { charging_infra: 30, subsidies: 40, manufacturing: 45, rnd: 33, mandates: 33, state_incentives: 33 },
  },
};

// Component
export default function PolicySimulator({ baseForecast }) {
  const requestAbortRef = useRef(null);
  const initialSliders = Object.fromEntries(SLIDER_CONFIG.map(s => [s.key, s.default]));
  const [sliders, setSliders] = useState(initialSliders);
  const [selectedPreset, setSelectedPreset] = useState('current_india');
  const [newPorts, setNewPorts] = useState(true);
  const [newHighways, setNewHighways] = useState(false);
  const [simResult, setSimResult] = useState(null);   // result from /api/run-simulation
  const [legacySim, setLegacySim] = useState(null);   // result from /api/policy-simulation/simulate
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [serverStatus, setServerStatus] = useState('unknown');
  const [simulationQuestion, setSimulationQuestion] = useState("India's EV market forecast to 2050");
  const [editingQuestion, setEditingQuestion] = useState(false);

  // Apply preset on first load
  useEffect(() => {
    setSliders(PRESETS.current_india.values);
    return () => {
      if (requestAbortRef.current) {
        requestAbortRef.current.abort();
      }
    };
  }, []);

  const handleSlider = (key, value) => {
    setSliders(prev => ({ ...prev, [key]: parseFloat(value) }));
    setSimResult(null);
    setLegacySim(null);
  };

  const applyPreset = (key) => {
    setSelectedPreset(key);
    setSliders(PRESETS[key].values);
    setSimResult(null);
    setLegacySim(null);
  };

  const applyQuestionToScenario = () => {
    const q = simulationQuestion.trim().toLowerCase();
    if (!q) {
      setEditingQuestion(false);
      return;
    }

    // Infer preset intent from user follow-up question.
    let inferredPreset = null;
    if (q.includes('china')) inferredPreset = 'china_model';
    else if (q.includes('aggressive')) inferredPreset = 'aggressive_growth';
    else if (q.includes('balanced')) inferredPreset = 'balanced';
    else if (q.includes('current') || q.includes('bau') || q.includes('business as usual')) inferredPreset = 'current_india';

    if (inferredPreset) {
      setSelectedPreset(inferredPreset);
      setSliders(PRESETS[inferredPreset].values);
    }

    const mentionsVs = q.includes(' vs ') || q.includes(' versus ');

    const mentionsPort = /(\bport\b|\bports\b|harbor|harbour)/.test(q);
    const deniesPort = /(without|no)\s+(new\s+)?ports?/.test(q) || /without\s+ports?/.test(q);

    const mentionsHighway = /(\bhighway\b|\bhighways\b|\broad\b|\broads\b|expressway)/.test(q);
    const deniesHighway = /(without|no)\s+(new\s+)?(highway|highways|road|roads)/.test(q) || /without\s+(highway|highways|road|roads)/.test(q);

    let nextPorts = newPorts;
    let nextHighways = newHighways;

    if (mentionsPort) {
      nextPorts = mentionsVs ? true : !deniesPort;
    }
    if (mentionsHighway) {
      nextHighways = mentionsVs ? true : !deniesHighway;
    }

    setNewPorts(nextPorts);
    setNewHighways(nextHighways);

    // Force chart into live-preview mode for instant visual response.
    setSimResult(null);
    setLegacySim(null);
    setError(null);
    setEditingQuestion(false);
  };

  // Compute live policy score for display
  const policyScore = SLIDER_CONFIG.reduce(
    (sum, s) => sum + sliders[s.key] * s.weight,
    0
  );

  const buildStandaloneProjection = (payload) => {
    const computedPolicyScore = (
      payload.charging_infra * 0.30 +
      payload.subsidies * 0.25 +
      payload.manufacturing * 0.20 +
      payload.rnd * 0.10 +
      payload.mandates * 0.10 +
      payload.state_incentives * 0.05
    );
    const currentValue = 4200000;
    const baseGrowthRate = 0.05;
    const policyGrowthBoost = (computedPolicyScore / 100) * 0.025;
    const portConstructionBoost    = payload.new_ports    ? 0.03  : 0;
    const highwayConstructionBoost = payload.new_highways ? 0.025 : 0;
    const effectiveGrowthRate = baseGrowthRate + policyGrowthBoost + portConstructionBoost + highwayConstructionBoost;
    const years = Array.from({ length: 26 }, (_, index) => 2025 + index);
    const withoutPolicy = years.map((_, index) => Math.round(currentValue * ((1 + baseGrowthRate) ** index)));
    const withPolicy = years.map((_, index) => Math.round(currentValue * ((1 + effectiveGrowthRate) ** index)));
    const delta = withPolicy[withPolicy.length - 1] - withoutPolicy[withoutPolicy.length - 1];

    const infraInsights = [];
    if (payload.new_ports)    infraInsights.push(`New port construction contributes ${(portConstructionBoost * 100).toFixed(2)}% additional annual growth.`);
    if (payload.new_highways) infraInsights.push(`New highway construction contributes ${(highwayConstructionBoost * 100).toFixed(2)}% additional annual growth.`);
    if (!payload.new_ports && !payload.new_highways) infraInsights.push('No new infrastructure construction uplift applied.');

    return {
      status: 'success',
      years,
      without_policy: withoutPolicy,
      with_policy: withPolicy,
      policy_score: Number(computedPolicyScore.toFixed(1)),
      base_growth_rate: Number((baseGrowthRate * 100).toFixed(2)),
      policy_growth_boost: Number((policyGrowthBoost * 100).toFixed(2)),
      port_construction_boost: Number((portConstructionBoost * 100).toFixed(2)),
      highway_construction_boost: Number((highwayConstructionBoost * 100).toFixed(2)),
      effective_growth_rate: Number((effectiveGrowthRate * 100).toFixed(2)),
      insights: [
        `Base growth starts at ${(baseGrowthRate * 100).toFixed(1)}% per year.`,
        `Policy mix contributes ${(policyGrowthBoost * 100).toFixed(2)}% additional annual growth.`,
        ...infraInsights,
        `By 2050 the with-policy scenario adds approximately ${delta.toLocaleString()} EV units over baseline.`,
      ],
      debug: {
        base_growth: Number(baseGrowthRate.toFixed(4)),
        policy_impact: Number(policyGrowthBoost.toFixed(4)),
        port_impact: Number(portConstructionBoost.toFixed(4)),
        highway_impact: Number(highwayConstructionBoost.toFixed(4)),
        final_growth: Number(effectiveGrowthRate.toFixed(4)),
        new_ports: payload.new_ports,
        new_highways: payload.new_highways,
      },
    };
  };

  const formatRequestError = (err, endpoint) => {
    if (axios.isCancel(err) || err?.code === 'ERR_CANCELED') {
      return 'Request was cancelled.';
    }
    if (err?.code === 'ECONNABORTED') {
      return `Request timeout after ${REQUEST_TIMEOUT_MS / 1000}s while calling ${endpoint}.`;
    }
    if (err?.response) {
      const serverMsg = err.response?.data?.error || err.response?.data?.message;
      return `Server error (${err.response.status}) from ${endpoint}${serverMsg ? `: ${serverMsg}` : ''}`;
    }
    if (err?.request) {
      return `Network error: backend unreachable at ${API_BASE_URL}. Check server/CORS/firewall.`;
    }
    return err?.message || 'Unknown request error.';
  };

  const checkServerAvailability = async (signal) => {
    try {
      const healthRes = await apiClient.get('/api/health', { signal });
      console.log('[PolicySimulator] health check response:', healthRes.data);
      setServerStatus('online');
      return true;
    } catch (err) {
      console.error('[PolicySimulator] health check failed:', err);
      setServerStatus('offline');
      throw new Error(`Backend server is not reachable at ${API_BASE_URL} (port 4000).`);
    }
  };

  const validatePayload = (payload) => {
    const invalidKey = Object.keys(payload).find((key) => {
      const value = payload[key];
      return Number.isNaN(Number(value)) || Number(value) < 0 || Number(value) > 100;
    });
    return !invalidKey
      ? { ok: true }
      : { ok: false, message: `Invalid payload value for '${invalidKey}'. Expected 0-100.` };
  };

  const fetchFallbackPost = async (endpoint, payload, signal) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    });
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Fetch fallback failed (${response.status}): ${errText}`);
    }
    return response.json();
  };

  const postWithRetry = async (endpoint, payload, signal) => {
    for (let attempt = 1; attempt <= MAX_RETRIES + 1; attempt += 1) {
      try {
        console.log(`[PolicySimulator] Attempt ${attempt} POST ${endpoint}`, payload);
        const res = await apiClient.post(endpoint, payload, { signal });
        console.log(`[PolicySimulator] Success POST ${endpoint}`, res.data);
        return res.data;
      } catch (err) {
        console.error(`[PolicySimulator] POST ${endpoint} failed on attempt ${attempt}`, err);
        console.error('[PolicySimulator] Full error object:', {
          message: err?.message,
          code: err?.code,
          status: err?.response?.status,
          data: err?.response?.data,
          stack: err?.stack,
        });

        if (axios.isCancel(err) || err?.code === 'ERR_CANCELED') {
          throw err;
        }

        const shouldRetry = !err?.response || err?.code === 'ECONNABORTED' || err?.response?.status >= 500;
        const isLast = attempt === MAX_RETRIES + 1;

        if (!shouldRetry && !isLast) {
          throw err;
        }

        if (isLast) {
          if (!err?.response) {
            console.warn(`[PolicySimulator] Trying fetch fallback for ${endpoint}`);
            return fetchFallbackPost(endpoint, payload, signal);
          }
          throw err;
        }

        await delay(400 * attempt);
      }
    }

    throw new Error('Retry loop exited unexpectedly');
  };

  const runStandalone = async (signal) => {
    const payload = {
      charging_infra: Number(sliders.charging_infra),
      subsidies: Number(sliders.subsidies),
      manufacturing: Number(sliders.manufacturing),
      rnd: Number(sliders.rnd),
      mandates: Number(sliders.mandates),
      state_incentives: Number(sliders.state_incentives),
      new_ports: newPorts,
      new_highways: newHighways,
    };

    const validation = validatePayload(payload);
    if (!validation.ok) {
      throw new Error(validation.message);
    }

    const data = await postWithRetry('/api/run-simulation', payload, signal);
    const localProjection = buildStandaloneProjection(payload);
    
    // Normalize response from different backends
    let normalizedData = data;
    if (data.forecast_data && !data.years) {
      // Transform minimal backend response to expected format
      const years = [];
      const without_policy = [];
      const with_policy = [];
      
      data.forecast_data.forEach(point => {
        years.push(2025 + Math.floor(point.month / 12));
        without_policy.push(point.base);
        with_policy.push(point.adjusted);
      });
      
      normalizedData = {
        ...data,
        years,
        without_policy,
        with_policy,
      };
    }

    const backendLooksOutdated =
      !normalizedData.port_construction_boost &&
      (!normalizedData.years || normalizedData.years[normalizedData.years.length - 1] < 2050);

    if (backendLooksOutdated) {
      normalizedData = {
        ...normalizedData,
        ...localProjection,
        source: 'client-standalone-fallback',
      };
    }

    console.log('Base Growth:', normalizedData.base_growth_rate);
    console.log('Policy Impact:', normalizedData.policy_growth_boost);
    console.log('Port Construction Impact:', normalizedData.port_construction_boost);
    console.log('Final Growth:', normalizedData.effective_growth_rate);
    console.log('New Ports Enabled:', newPorts);
    
    setSimResult(normalizedData);
  };

  const handleRunSimulation = async () => {
    if (requestAbortRef.current) {
      requestAbortRef.current.abort();
    }

    const controller = new AbortController();
    requestAbortRef.current = controller;

    setLoading(true);
    setError(null);
    setSimResult(null);
    setLegacySim(null);

    try {
      await checkServerAvailability(controller.signal);

      if (baseForecast && baseForecast.length > 0) {
        const scaledAdjustments = {};
        SLIDER_CONFIG.forEach((s) => {
          scaledAdjustments[s.policyKey] = parseFloat(((sliders[s.key] / 100) * 30).toFixed(1));
        });
        scaledAdjustments.import_duties = 5;

        const legacyPayload = {
          base_forecast: baseForecast,
          policy_adjustments: scaledAdjustments,
        };
        const data = await postWithRetry('/api/policy-simulation/simulate', legacyPayload, controller.signal);
        setLegacySim(data.simulation);
      } else {
        await runStandalone(controller.signal);
      }
    } catch (err) {
      const endpointHint = baseForecast && baseForecast.length > 0
        ? '/api/policy-simulation/simulate'
        : '/api/run-simulation';
      const message = formatRequestError(err, endpointHint);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelRequest = () => {
    if (requestAbortRef.current) {
      requestAbortRef.current.abort();
      setLoading(false);
      setError('Simulation request cancelled by user.');
    }
  };

  // Live chart projection — reacts instantly to slider / checkbox changes
  const liveChartPoints = (() => {
    const computedPolicyScore = SLIDER_CONFIG.reduce(
      (sum, s) => sum + sliders[s.key] * s.weight,
      0
    );
    const currentValue = 4200000;
    const baseGrowthRate = 0.05;
    const policyGrowthBoost = (computedPolicyScore / 100) * 0.025;
    const portBoost    = newPorts    ? 0.03  : 0;
    const highwayBoost = newHighways ? 0.025 : 0;
    const effectiveRate = baseGrowthRate + policyGrowthBoost + portBoost + highwayBoost;
    const years = Array.from({ length: 26 }, (_, i) => 2025 + i);
    return years.map((yr, i) => ({
      year: yr,
      original: Math.round(currentValue * ((1 + baseGrowthRate) ** i)),
      adjusted: Math.round(currentValue * ((1 + effectiveRate) ** i)),
    }));
  })();

  // Chart data helpers
  // Use API result if available, otherwise fall back to live projection
  const chartPoints = (() => {
    if (simResult && simResult.years && Array.isArray(simResult.years)) {
      return simResult.years.map((yr, i) => ({
        year: yr,
        original: simResult.without_policy?.[i] || 0,
        adjusted: simResult.with_policy?.[i] || 0,
      }));
    }
    if (legacySim?.simulated_data) {
      const yearly = {};
      legacySim.simulated_data.forEach(pt => {
        const period = pt.period;
        let yr = typeof period === 'string' ? parseInt(period.split('-')[0], 10) : 2025 + Math.floor((period || 0) / 12);
        if (!yearly[yr]) yearly[yr] = { orig: [], adj: [] };
        yearly[yr].orig.push(pt.original_forecast);
        yearly[yr].adj.push(pt.adjusted_forecast);
      });
      return Object.keys(yearly).sort().map(yr => ({
        year: parseInt(yr, 10),
        original: Math.round(yearly[yr].orig.reduce((a, b) => a + b, 0) / yearly[yr].orig.length),
        adjusted: Math.round(yearly[yr].adj.reduce((a, b) => a + b, 0) / yearly[yr].adj.length),
      }));
    }
    // No API result yet — show live projection
    return liveChartPoints;
  })();

  const advancedVizData = (() => {
    if (!chartPoints.length) {
      return { gapPoints: [], growthPoints: [], snapshotPoints: [], cumulativeGain: 0 };
    }

    const gapPoints = chartPoints.map((p) => ({
      year: p.year,
      gain: Math.max(0, p.adjusted - p.original),
    }));

    const growthPoints = chartPoints
      .map((p, i) => {
        if (i === 0) {
          return { year: p.year, baseGrowth: null, policyGrowth: null };
        }
        const prev = chartPoints[i - 1];
        const baseGrowth = prev.original > 0 ? ((p.original - prev.original) / prev.original) * 100 : 0;
        const policyGrowth = prev.adjusted > 0 ? ((p.adjusted - prev.adjusted) / prev.adjusted) * 100 : 0;
        return {
          year: p.year,
          baseGrowth,
          policyGrowth,
        };
      })
      .filter((p) => p.baseGrowth !== null && p.policyGrowth !== null);

    const milestoneYears = [2025, 2030, 2035, 2040, 2045, 2050];
    const snapshotPoints = milestoneYears
      .map((yr) => chartPoints.find((p) => p.year === yr))
      .filter(Boolean);

    const cumulativeGain = gapPoints.reduce((sum, p) => sum + p.gain, 0);

    return { gapPoints, growthPoints, snapshotPoints, cumulativeGain };
  })();

  const hasResult = simResult || legacySim;
  const insights  = simResult?.insights ?? legacySim?.insights ?? [];
  const comparisonLabels = (() => {
    if (newPorts && newHighways) return { baseline: 'Without New Infrastructure', adjusted: 'With New Ports + Highways' };
    if (newPorts)    return { baseline: 'Without New Port Construction',    adjusted: 'With New Port Construction' };
    if (newHighways) return { baseline: 'Without New Highway Construction', adjusted: 'With New Highway Construction' };
    return { baseline: 'Base Growth Only', adjusted: 'Policy Mix Applied' };
  })();

  const compStats = (() => {
    if (simResult && simResult.years && Array.isArray(simResult.years) && simResult.years.length > 0) {
      const last = simResult.years.length - 1;
      const orig = simResult.without_policy?.[last] || 0;
      const adj  = simResult.with_policy?.[last] || 0;
      return {
        original:   orig,
        simulated:  adj,
        change:     adj - orig,
        pct:        orig > 0 ? (((adj - orig) / orig) * 100).toFixed(1) : 0,
        effectiveGrowth: simResult.effective_growth_rate || 0,
        score: simResult.policy_score || 0,
      };
    }
    if (legacySim?.comparison) {
      const c = legacySim.comparison;
      return {
        original:   Math.round(c.original_end_value),
        simulated:  Math.round(c.simulated_end_value),
        change:     Math.round(c.total_change),
        pct:        c.percentage_improvement.toFixed(1),
        effectiveGrowth: null,
        score: null,
      };
    }
    return null;
  })();

  // SVG chart renderer
  const SimChart = ({ points }) => {
    if (!points.length) return null;
    const W = 820, H = 320, PL = 90, PT = 30, PR = 30, PB = 60;
    const plotW = W - PL - PR;
    const plotH = H - PT - PB;
    const maxVal = Math.max(...points.map(p => Math.max(p.original, p.adjusted)));
    const minVal = Math.min(...points.map(p => Math.min(p.original, p.adjusted))) * 0.95;
    const cx = i => PL + (i / (points.length - 1 || 1)) * plotW;
    const cy = v => PT + plotH - ((v - minVal) / (maxVal - minVal || 1)) * plotH;

    return (
      <div className="w-full overflow-x-auto">
        <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} style={{ minWidth: 340 }}>
          {/* Grid */}
          {[0,1,2,3,4].map(i => {
            const yv = minVal + (i / 4) * (maxVal - minVal);
            const yp = cy(yv);
            return (
              <g key={i}>
                <line x1={PL} y1={yp} x2={PL+plotW} y2={yp} stroke="#e5e7eb" strokeWidth="1" strokeDasharray="4" />
                <text x={PL-8} y={yp+4} fontSize="11" fill="#9ca3af" textAnchor="end">
                  {(yv/1000000).toFixed(1)}M
                </text>
              </g>
            );
          })}

          {/* Axes */}
          <line x1={PL} y1={PT} x2={PL} y2={PT+plotH} stroke="#6b7280" strokeWidth="2" />
          <line x1={PL} y1={PT+plotH} x2={PL+plotW} y2={PT+plotH} stroke="#6b7280" strokeWidth="2" />

          {/* Original line */}
          {points.map((p, i) => i > 0 && (
            <line key={`o${i}`}
              x1={cx(i-1)} y1={cy(points[i-1].original)}
              x2={cx(i)}   y2={cy(p.original)}
              stroke="#2563eb" strokeWidth="3"
            />
          ))}

          {/* Adjusted / with-policy line */}
          {points.map((p, i) => i > 0 && (
            <line key={`a${i}`}
              x1={cx(i-1)} y1={cy(points[i-1].adjusted)}
              x2={cx(i)}   y2={cy(p.adjusted)}
              stroke="#059669" strokeWidth="3.5" strokeDasharray="10,5"
            />
          ))}

          {/* Points + labels */}
          {points.map((p, i) => (
            <g key={i}>
              <circle cx={cx(i)} cy={cy(p.original)} r="5" fill="#3b82f6" stroke="white" strokeWidth="2" />
              <circle cx={cx(i)} cy={cy(p.adjusted)} r="5" fill="#10b981" stroke="white" strokeWidth="2" />
              <text x={cx(i)} y={PT+plotH+18} fontSize="12" textAnchor="middle" fill="#374151" fontWeight="600">
                {p.year}
              </text>
            </g>
          ))}

          {/* Y-axis label */}
          <text transform={`rotate(-90)`} x={-(PT+plotH/2)} y={18}
            fontSize="12" fill="#6b7280" fontWeight="600" textAnchor="middle">
            Units
          </text>

          {/* Legend (stacked to avoid text overlap with long scenario labels) */}
          <rect
            x={PL + 12}
            y={8}
            width={Math.min(plotW - 24, 520)}
            height={38}
            rx="6"
            fill="white"
            fillOpacity="0.9"
          />

          <line x1={PL + 24} y1={20} x2={PL + 54} y2={20} stroke="#3b82f6" strokeWidth="2.5" />
          <circle cx={PL + 39} cy={20} r="4" fill="#3b82f6" />
          <text x={PL + 62} y={24} fontSize="12" fill="#374151">{comparisonLabels.baseline}</text>

          <line x1={PL + 24} y1={36} x2={PL + 54} y2={36} stroke="#10b981" strokeWidth="2.5" strokeDasharray="7,4" />
          <circle cx={PL + 39} cy={36} r="4" fill="#10b981" />
          <text x={PL + 62} y={40} fontSize="12" fill="#374151">{comparisonLabels.adjusted}</text>
        </svg>
      </div>
    );
  };

  const GapTrendChart = ({ points }) => {
    if (!points.length) return null;
    const W = 820, H = 250, PL = 70, PT = 20, PR = 20, PB = 45;
    const plotW = W - PL - PR;
    const plotH = H - PT - PB;
    const maxVal = Math.max(...points.map((p) => p.gain), 1);
    const cx = (i) => PL + (i / (points.length - 1 || 1)) * plotW;
    const cy = (v) => PT + plotH - (v / maxVal) * plotH;

    const areaPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${cx(i)} ${cy(p.gain)}`).join(' ');
    const areaFill = `${areaPath} L ${cx(points.length - 1)} ${PT + plotH} L ${cx(0)} ${PT + plotH} Z`;

    return (
      <div className="w-full overflow-x-auto">
        <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} style={{ minWidth: 340 }}>
          {[0, 1, 2, 3, 4].map((i) => {
            const yv = (i / 4) * maxVal;
            const yp = cy(yv);
            return (
              <g key={i}>
                <line x1={PL} y1={yp} x2={PL + plotW} y2={yp} stroke="#e5e7eb" strokeWidth="1" strokeDasharray="4" />
                <text x={PL - 8} y={yp + 4} fontSize="11" fill="#9ca3af" textAnchor="end">{(yv / 1000000).toFixed(1)}M</text>
              </g>
            );
          })}

          <line x1={PL} y1={PT} x2={PL} y2={PT + plotH} stroke="#6b7280" strokeWidth="2" />
          <line x1={PL} y1={PT + plotH} x2={PL + plotW} y2={PT + plotH} stroke="#6b7280" strokeWidth="2" />

          <path d={areaFill} fill="#a7f3d0" fillOpacity="0.5" />
          <path d={areaPath} fill="none" stroke="#059669" strokeWidth="3" />

          {points.map((p, i) => (
            <g key={p.year}>
              <circle cx={cx(i)} cy={cy(p.gain)} r="3.5" fill="#10b981" />
              {i % 5 === 0 || i === points.length - 1 ? (
                <text x={cx(i)} y={PT + plotH + 16} fontSize="11" fill="#6b7280" textAnchor="middle">{p.year}</text>
              ) : null}
            </g>
          ))}
        </svg>
      </div>
    );
  };

  const GrowthRateChart = ({ points }) => {
    if (!points.length) return null;
    const W = 820, H = 250, PL = 70, PT = 20, PR = 20, PB = 45;
    const plotW = W - PL - PR;
    const plotH = H - PT - PB;
    const maxVal = Math.max(...points.map((p) => Math.max(p.baseGrowth, p.policyGrowth)), 1);
    const minVal = Math.min(...points.map((p) => Math.min(p.baseGrowth, p.policyGrowth)), 0);
    const cx = (i) => PL + (i / (points.length - 1 || 1)) * plotW;
    const cy = (v) => PT + plotH - ((v - minVal) / (maxVal - minVal || 1)) * plotH;

    return (
      <div className="w-full overflow-x-auto">
        <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} style={{ minWidth: 340 }}>
          {[0, 1, 2, 3, 4].map((i) => {
            const yv = minVal + (i / 4) * (maxVal - minVal);
            const yp = cy(yv);
            return (
              <g key={i}>
                <line x1={PL} y1={yp} x2={PL + plotW} y2={yp} stroke="#e5e7eb" strokeWidth="1" strokeDasharray="4" />
                <text x={PL - 8} y={yp + 4} fontSize="11" fill="#9ca3af" textAnchor="end">{yv.toFixed(1)}%</text>
              </g>
            );
          })}

          <line x1={PL} y1={PT} x2={PL} y2={PT + plotH} stroke="#6b7280" strokeWidth="2" />
          <line x1={PL} y1={PT + plotH} x2={PL + plotW} y2={PT + plotH} stroke="#6b7280" strokeWidth="2" />

          {points.map((p, i) => i > 0 && (
            <line
              key={`gb${p.year}`}
              x1={cx(i - 1)} y1={cy(points[i - 1].baseGrowth)}
              x2={cx(i)} y2={cy(p.baseGrowth)}
              stroke="#2563eb" strokeWidth="2.5"
            />
          ))}
          {points.map((p, i) => i > 0 && (
            <line
              key={`gp${p.year}`}
              x1={cx(i - 1)} y1={cy(points[i - 1].policyGrowth)}
              x2={cx(i)} y2={cy(p.policyGrowth)}
              stroke="#7c3aed" strokeWidth="2.5" strokeDasharray="6,4"
            />
          ))}

          {points.map((p, i) => (
            <g key={`pt-${p.year}`}>
              <circle cx={cx(i)} cy={cy(p.baseGrowth)} r="3" fill="#3b82f6" />
              <circle cx={cx(i)} cy={cy(p.policyGrowth)} r="3" fill="#8b5cf6" />
              {i % 5 === 0 || i === points.length - 1 ? (
                <text x={cx(i)} y={PT + plotH + 16} fontSize="11" fill="#6b7280" textAnchor="middle">{p.year}</text>
              ) : null}
            </g>
          ))}
        </svg>
      </div>
    );
  };

  const MilestoneBarsChart = ({ points }) => {
    if (!points.length) return null;
    const W = 820, H = 280, PL = 70, PT = 20, PR = 20, PB = 55;
    const plotW = W - PL - PR;
    const plotH = H - PT - PB;
    const maxVal = Math.max(...points.map((p) => Math.max(p.original, p.adjusted)), 1);
    const groupW = plotW / points.length;
    const barW = Math.max(8, groupW * 0.28);
    const cy = (v) => PT + plotH - (v / maxVal) * plotH;

    return (
      <div className="w-full overflow-x-auto">
        <svg width="100%" height={H} viewBox={`0 0 ${W} ${H}`} style={{ minWidth: 340 }}>
          {[0, 1, 2, 3, 4].map((i) => {
            const yv = (i / 4) * maxVal;
            const yp = cy(yv);
            return (
              <g key={i}>
                <line x1={PL} y1={yp} x2={PL + plotW} y2={yp} stroke="#e5e7eb" strokeWidth="1" strokeDasharray="4" />
                <text x={PL - 8} y={yp + 4} fontSize="11" fill="#9ca3af" textAnchor="end">{(yv / 1000000).toFixed(1)}M</text>
              </g>
            );
          })}

          <line x1={PL} y1={PT} x2={PL} y2={PT + plotH} stroke="#6b7280" strokeWidth="2" />
          <line x1={PL} y1={PT + plotH} x2={PL + plotW} y2={PT + plotH} stroke="#6b7280" strokeWidth="2" />

          {points.map((p, i) => {
            const gx = PL + i * groupW + groupW / 2;
            const baseX = gx - barW - 3;
            const adjX = gx + 3;
            const baseY = cy(p.original);
            const adjY = cy(p.adjusted);
            return (
              <g key={`bar-${p.year}`}>
                <rect x={baseX} y={baseY} width={barW} height={PT + plotH - baseY} fill="#60a5fa" rx="2" />
                <rect x={adjX} y={adjY} width={barW} height={PT + plotH - adjY} fill="#34d399" rx="2" />
                <text x={gx} y={PT + plotH + 18} fontSize="11" fill="#6b7280" textAnchor="middle">{p.year}</text>
              </g>
            );
          })}
        </svg>
      </div>
    );
  };

  // Score color helper
  const scoreColor = policyScore >= 65 ? 'text-green-600' : policyScore >= 35 ? 'text-yellow-600' : 'text-red-600';

  // Render
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 mt-6">

      {/* Header */}
      <div className="mb-5">
        <h3 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          Interactive Policy Simulator
          {!baseForecast?.length && (
            <span className="text-xs font-normal bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
              Standalone mode
            </span>
          )}
          <span className={`text-xs font-normal px-2 py-0.5 rounded-full ${
            serverStatus === 'online'
              ? 'bg-green-100 text-green-700'
              : serverStatus === 'offline'
                ? 'bg-red-100 text-red-700'
                : 'bg-gray-100 text-gray-600'
          }`}>
            Backend: {serverStatus}
          </span>
        </h3>
        <div className="mt-2">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Simulation Question</p>
          {editingQuestion ? (
            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <input
                type="text"
                value={simulationQuestion}
                onChange={(e) => setSimulationQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    applyQuestionToScenario();
                  }
                  if (e.key === 'Escape') {
                    setEditingQuestion(false);
                  }
                }}
                autoFocus
                className="flex-1 text-sm border border-blue-400 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-300 text-gray-700"
                placeholder="e.g. India car sales forecast to 2050"
              />
              <div className="flex items-center gap-2">
                <button
                  onClick={applyQuestionToScenario}
                  className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >Apply</button>
                <button
                  onClick={() => setEditingQuestion(false)}
                  className="text-xs px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >Cancel</button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row sm:items-center gap-2">
              <p className="text-gray-700 text-sm font-medium break-words">{simulationQuestion}</p>
              <button
                onClick={() => setEditingQuestion(true)}
                className="text-xs px-2.5 py-1 text-blue-600 border border-blue-300 rounded hover:bg-blue-50 transition-colors w-fit"
              >Change Question</button>
            </div>
          )}
          <p className="text-gray-400 text-xs mt-1">
            Edit question and press <strong className="text-gray-500">Enter/Apply</strong> for instant preview. Click <strong className="text-gray-500">Run Simulation</strong> for official backend result.
          </p>
        </div>
      </div>

      {/* Presets */}
      <div className="mb-5">
        <p className="text-sm font-semibold text-gray-600 mb-2">Quick Presets</p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {Object.entries(PRESETS).map(([k, p]) => (
            <button
              key={k}
              onClick={() => applyPreset(k)}
              className={`p-2.5 rounded-lg border-2 text-left transition-all text-sm ${
                selectedPreset === k
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
              }`}
            >
              <div className="font-semibold">{p.name}</div>
              <div className="text-xs text-gray-500 mt-0.5 leading-snug">{p.description}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="mb-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
        <p className="text-sm font-semibold text-emerald-900 mb-2">Infrastructure Boost Scenarios</p>
        <p className="text-sm text-emerald-800 mb-3">
          Enable one or both infrastructure types to add an annual growth uplift on top of the baseline rate and policy mix.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <label className="inline-flex items-start gap-2 text-sm text-emerald-900 cursor-pointer">
            <input
              type="checkbox"
              checked={newPorts}
              onChange={(e) => { setNewPorts(e.target.checked); setSimResult(null); setLegacySim(null); }}
              className="h-4 w-4 mt-0.5 rounded border-emerald-400 text-emerald-600 focus:ring-emerald-500"
            />
            <span>
              <span className="font-semibold">New Port Construction</span>
              <span className="block text-xs text-emerald-700">+3.0% dedicated logistics uplift per year</span>
            </span>
          </label>
          <label className="inline-flex items-start gap-2 text-sm text-emerald-900 cursor-pointer">
            <input
              type="checkbox"
              checked={newHighways}
              onChange={(e) => { setNewHighways(e.target.checked); setSimResult(null); setLegacySim(null); }}
              className="h-4 w-4 mt-0.5 rounded border-emerald-400 text-emerald-600 focus:ring-emerald-500"
            />
            <span>
              <span className="font-semibold">New Highway Construction</span>
              <span className="block text-xs text-emerald-700">+2.5% connectivity & distribution uplift per year</span>
            </span>
          </label>
        </div>
      </div>

      {/* Sliders */}
      <div className="mb-5">
        <div className="flex justify-between items-center mb-3">
          <p className="text-sm font-semibold text-gray-600">Policy Levers (0-100)</p>
          <div className="text-sm">
            Policy Score: <span className={`font-bold text-base ${scoreColor}`}>{policyScore.toFixed(0)}</span>
            <span className="text-gray-400">/100</span>
          </div>
        </div>

        <div className="space-y-4">
          {SLIDER_CONFIG.map(s => (
            <div key={s.key} className="bg-gray-50 rounded-xl p-4">
              <div className="flex justify-between items-center mb-1">
                <label className="text-sm font-semibold text-gray-700">{s.label}</label>
                <span className={`text-lg font-bold tabular-nums ${
                  sliders[s.key] >= 65 ? 'text-green-600' :
                  sliders[s.key] >= 35 ? 'text-yellow-600' : 'text-red-500'
                }`}>{sliders[s.key].toFixed(0)}</span>
              </div>
              <p className="text-xs text-gray-400 mb-2">{s.description}</p>
              <input
                type="range"
                min={s.min} max={s.max} step="1"
                value={sliders[s.key]}
                onChange={e => handleSlider(s.key, e.target.value)}
                className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0 - Low</span>
                <span>50 - Medium</span>
                <span>100 - High</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chart — always visible, updates live with sliders */}
      <div className="bg-gray-50 rounded-2xl p-5 mb-5">
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-semibold text-gray-700">{simulationQuestion} — Comparison (2025–2050)</h4>
          {!hasResult && (
            <span className="text-xs text-gray-400 italic">Live preview — click Run Simulation for official result</span>
          )}
        </div>
        <SimChart points={chartPoints} />
      </div>

      {/* Advanced charts */}
      <div className="grid grid-cols-1 gap-4 mb-5">
        <div className="bg-gray-50 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-gray-700">Policy Gain Over Time</h4>
            <span className="text-xs text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
              Cumulative gain: {Math.round(advancedVizData.cumulativeGain).toLocaleString()} units
            </span>
          </div>
          <p className="text-xs text-gray-500 mb-2">Shows additional units generated each year by selected policy + infrastructure scenario.</p>
          <GapTrendChart points={advancedVizData.gapPoints} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-2xl p-5">
            <h4 className="font-semibold text-gray-700 mb-2">Annual Growth Rate Trend</h4>
            <p className="text-xs text-gray-500 mb-2">Blue = baseline growth, purple = scenario growth (year-over-year %).</p>
            <GrowthRateChart points={advancedVizData.growthPoints} />
          </div>

          <div className="bg-gray-50 rounded-2xl p-5">
            <h4 className="font-semibold text-gray-700 mb-2">Milestone Year Snapshot</h4>
            <p className="text-xs text-gray-500 mb-2">Grouped bars for 2025/2030/2035/2040/2045/2050 to compare baseline vs scenario quickly.</p>
            <MilestoneBarsChart points={advancedVizData.snapshotPoints} />
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm flex items-start gap-2">
          <span className="shrink-0">Warning</span>
          <span>{error}</span>
        </div>
      )}

      {/* Run button */}
      <button
        onClick={handleRunSimulation}
        disabled={loading}
        className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 px-6 rounded-xl font-bold text-base
          hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500
          disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Running Simulation...
          </span>
        ) : 'Run Simulation'}
      </button>

      {loading && (
        <button
          type="button"
          onClick={handleCancelRequest}
          className="w-full mt-2 bg-gray-100 hover:bg-gray-200 text-gray-700 py-2 px-4 rounded-lg text-sm font-medium transition"
        >
          Cancel Request
        </button>
      )}

      {/* Results */}
      {hasResult && (
        <div className="mt-6 space-y-5">

          {/* KPI strip */}
          {compStats && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: `${comparisonLabels.baseline} (2050)`, value: compStats.original.toLocaleString(), bg: 'bg-blue-50',   text: 'text-blue-800' },
                { label: `${comparisonLabels.adjusted} (2050)`, value: compStats.simulated.toLocaleString(), bg: 'bg-green-50',  text: 'text-green-700' },
                { label: 'Additional Units by 2050', value: `+${compStats.change.toLocaleString()}`, bg: 'bg-purple-50', text: 'text-purple-700' },
                { label: 'Growth Uplift',         value: `+${compStats.pct}%`,                   bg: 'bg-orange-50', text: 'text-orange-700' },
              ].map(k => (
                <div key={k.label} className={`${k.bg} rounded-xl p-4`}>
                  <p className="text-xs text-gray-500 mb-1">{k.label}</p>
                  <p className={`text-xl font-bold ${k.text}`}>{k.value}</p>
                </div>
              ))}
            </div>
          )}
          {compStats?.effectiveGrowth != null && (
            <div className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
              <p className="text-center">
                Effective annual growth rate: <span className="font-bold text-blue-700">{compStats.effectiveGrowth}%</span>
              </p>
              <p className="text-center mt-1">
                Formula: <span className="font-semibold">future_value = current_value * (1 + growth_rate) ^ years</span>
              </p>
              {simResult && (
                <p className="text-center mt-1">
                  Base {simResult.base_growth_rate}% + Policy mix {simResult.policy_growth_boost}%{simResult.port_construction_boost > 0 ? ` + Port construction ${simResult.port_construction_boost}%` : ''}{simResult.highway_construction_boost > 0 ? ` + Highway construction ${simResult.highway_construction_boost}%` : ''}
                </p>
              )}
            </div>
          )}

          {/* Insights */}
          {insights.length > 0 && (
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-5">
              <h4 className="font-semibold text-gray-800 mb-3">Strategic Insights</h4>
              <ul className="space-y-2">
                {insights.map((ins, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="shrink-0 mt-0.5">-</span>
                    <span>{ins}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
