import React, { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { apiGet, apiPost } from "../api";

function formatMoney(value) {
  return `$${Math.round(value).toLocaleString()}`;
}

function safeNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function NumberPill({ label, value }) {
  return (
    <div className="pill">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function LoadingSkeleton({ lines = 4 }) {
  return (
    <div className="skeleton-wrap" aria-hidden="true">
      {Array.from({ length: lines }).map((_, index) => (
        <div key={index} className="skeleton-line" />
      ))}
    </div>
  );
}

export default function AnalysisApp() {
  const THEME_PRESETS = [
    { id: "aurora", label: "Aurora" },
    { id: "oceanic", label: "Oceanic" },
    { id: "carbon-neon", label: "Carbon Neon" },
  ];

  const TAB_GROUPS = [
    {
      id: "market",
      label: "Market",
      tabs: [
        { id: "trending", label: "Trending", icon: "TR" },
        { id: "deals", label: "Deals", icon: "DL" },
        { id: "news", label: "News", icon: "NW" },
        { id: "comps", label: "Comps", icon: "CP" },
      ],
    },
    {
      id: "analysis",
      label: "Analysis",
      tabs: [
        { id: "comparison", label: "Comparison", icon: "CM" },
        { id: "calculators", label: "Calculators", icon: "CL" },
        { id: "monitor", label: "Monitor", icon: "MN" },
        { id: "strategy", label: "Strategy", icon: "ST" },
        { id: "briefs", label: "Briefs", icon: "BF" },
      ],
    },
    {
      id: "execution",
      label: "Execution",
      tabs: [
        { id: "pipeline", label: "Pipeline", icon: "PL" },
        { id: "watchlist", label: "Watchlist", icon: "WL" },
        { id: "reports", label: "Reports", icon: "RP" },
      ],
    },
  ];

  const STORAGE_KEYS = {
    watchlist: "signalestate_watchlist",
    pipeline: "signalestate_pipeline",
    reports: "signalestate_reports",
    strategy: "signalestate_strategy",
    artifacts: "signalestate_artifacts",
    theme: "signalestate_theme",
    nav: "signalestate_nav",
    liquidGlass: "signalestate_liquid_glass",
  };

  const [properties, setProperties] = useState([]);
  const [rankings, setRankings] = useState([]);
  const [activeTab, setActiveTab] = useState("trending");
  const [activeGroup, setActiveGroup] = useState("market");
  const [selectedPropertyId, setSelectedPropertyId] = useState("");
  const [comparePropertyId, setComparePropertyId] = useState("");
  const [compAnchorId, setCompAnchorId] = useState("");
  const [valuation, setValuation] = useState(null);
  const [compareValuation, setCompareValuation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [backendStatus, setBackendStatus] = useState("checking");
  const [healthData, setHealthData] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [pipelineMap, setPipelineMap] = useState({});
  const [savedReports, setSavedReports] = useState([]);
  const [strategyMode, setStrategyMode] = useState("balanced");
  const [themePreset, setThemePreset] = useState("oceanic");
  const [liquidGlass, setLiquidGlass] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [commandQuery, setCommandQuery] = useState("");
  const [commandFocusIndex, setCommandFocusIndex] = useState(0);
  const [recentTabs, setRecentTabs] = useState(["trending"]);
  const [artifacts, setArtifacts] = useState([]);
  const [researchPack, setResearchPack] = useState(null);
  const [researchLoading, setResearchLoading] = useState(false);
  const [portfolioRisk, setPortfolioRisk] = useState(null);
  const [portfolioRiskLoading, setPortfolioRiskLoading] = useState(false);
  const [tabIndicator, setTabIndicator] = useState({ left: 0, width: 0 });
  const [calculator, setCalculator] = useState({
    price: 900000,
    depositPct: 20,
    interestPct: 6.1,
    years: 30,
    weeklyRent: 1100,
    monthlyCosts: 1200,
  });

  const tabRowRef = useRef(null);
  const groupRowRef = useRef(null);
  const tabButtonRefs = useRef({});
  const groupButtonRefs = useRef({});

  function updateActiveIndicators() {
    if (tabRowRef.current) {
      const active = tabButtonRefs.current[activeTab];
      if (active) {
        setTabIndicator({ left: active.offsetLeft, width: active.offsetWidth });
      }
    }
  }

  function updateActiveIndicatorsDeferred() {
    // Layout can shift after async data/font paint in production builds.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        updateActiveIndicators();
      });
    });
  }

  useEffect(() => {
    try {
      const savedWatchlist = JSON.parse(localStorage.getItem(STORAGE_KEYS.watchlist) || "[]");
      const savedPipeline = JSON.parse(localStorage.getItem(STORAGE_KEYS.pipeline) || "{}");
      const reports = JSON.parse(localStorage.getItem(STORAGE_KEYS.reports) || "[]");
      const artifactList = JSON.parse(localStorage.getItem(STORAGE_KEYS.artifacts) || "[]");
      const strategy = localStorage.getItem(STORAGE_KEYS.strategy);
      const theme = localStorage.getItem(STORAGE_KEYS.theme);
      const glass = localStorage.getItem(STORAGE_KEYS.liquidGlass);
      const navState = JSON.parse(localStorage.getItem(STORAGE_KEYS.nav) || "{}");
      if (Array.isArray(savedWatchlist)) setWatchlist(savedWatchlist);
      if (savedPipeline && typeof savedPipeline === "object") setPipelineMap(savedPipeline);
      if (Array.isArray(reports)) setSavedReports(reports);
      if (Array.isArray(artifactList)) setArtifacts(artifactList);
      if (strategy) setStrategyMode(strategy);
      if (theme) setThemePreset(theme);
      if (glass) setLiquidGlass(glass === "on");
      if (navState && typeof navState === "object") {
        if (typeof navState.activeGroup === "string") setActiveGroup(navState.activeGroup);
        if (typeof navState.activeTab === "string") setActiveTab(navState.activeTab);
        if (Array.isArray(navState.recentTabs) && navState.recentTabs.length > 0) {
          setRecentTabs(navState.recentTabs.slice(0, 6));
        }
      }
    } catch {
      setWatchlist([]);
      setPipelineMap({});
      setSavedReports([]);
      setArtifacts([]);
    }
  }, [
    STORAGE_KEYS.artifacts,
    STORAGE_KEYS.liquidGlass,
    STORAGE_KEYS.nav,
    STORAGE_KEYS.pipeline,
    STORAGE_KEYS.reports,
    STORAGE_KEYS.strategy,
    STORAGE_KEYS.theme,
    STORAGE_KEYS.watchlist,
  ]);

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEYS.nav,
      JSON.stringify({
        activeGroup,
        activeTab,
        recentTabs,
      }),
    );
  }, [STORAGE_KEYS.nav, activeGroup, activeTab, recentTabs]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", themePreset);
  }, [themePreset]);

  useEffect(() => {
    document.documentElement.setAttribute("data-liquid-glass", liquidGlass ? "on" : "off");
    localStorage.setItem(STORAGE_KEYS.liquidGlass, liquidGlass ? "on" : "off");
  }, [STORAGE_KEYS.liquidGlass, liquidGlass]);

  useLayoutEffect(() => {
    updateActiveIndicatorsDeferred();
  }, [activeTab, activeGroup]);

  useEffect(() => {
    updateActiveIndicatorsDeferred();

    const onResize = () => updateActiveIndicatorsDeferred();
    window.addEventListener("resize", onResize);

    let tabResizeObserver;
    const tabRow = tabRowRef.current;
    const active = tabButtonRefs.current[activeTab];
    if (typeof ResizeObserver !== "undefined") {
      tabResizeObserver = new ResizeObserver(() => updateActiveIndicatorsDeferred());
      if (tabRow) tabResizeObserver.observe(tabRow);
      if (active) tabResizeObserver.observe(active);
    }

    const fonts = document.fonts;
    if (fonts && typeof fonts.ready?.then === "function") {
      fonts.ready.then(() => updateActiveIndicatorsDeferred());
    }

    return () => {
      window.removeEventListener("resize", onResize);
      if (tabResizeObserver) tabResizeObserver.disconnect();
    };
  }, [activeTab, activeGroup]);

  useEffect(() => {
    setRecentTabs((prev) => [activeTab, ...prev.filter((item) => item !== activeTab)].slice(0, 6));
  }, [activeTab]);

  useEffect(() => {
    const handleGlobalKeys = (event) => {
      const target = event.target;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable)) {
        return;
      }
      const currentGroupTabs = (TAB_GROUPS.find((group) => group.id === activeGroup) || TAB_GROUPS[0] || { tabs: [] }).tabs;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen(true);
        setCommandQuery("");
        setCommandFocusIndex(0);
      }
      if (event.altKey && /^[1-9]$/.test(event.key)) {
        const index = Number(event.key) - 1;
        const quickTab = currentGroupTabs[index];
        if (quickTab) {
          event.preventDefault();
          selectTab(activeGroup, quickTab.id);
        }
      }
      if (event.altKey && (event.key === "ArrowRight" || event.key === "ArrowLeft")) {
        const tabIds = currentGroupTabs.map((tab) => tab.id);
        if (!tabIds.length) return;
        const currentIndex = Math.max(tabIds.indexOf(activeTab), 0);
        const nextIndex =
          event.key === "ArrowRight"
            ? (currentIndex + 1) % tabIds.length
            : (currentIndex - 1 + tabIds.length) % tabIds.length;
        event.preventDefault();
        selectTab(activeGroup, tabIds[nextIndex]);
      }
      if (event.altKey && (event.key === "g" || event.key === "G")) {
        const groupIds = TAB_GROUPS.map((group) => group.id);
        const currentIndex = Math.max(groupIds.indexOf(activeGroup), 0);
        const nextIndex = (currentIndex + 1) % groupIds.length;
        event.preventDefault();
        selectGroup(groupIds[nextIndex]);
      }
      if (event.key === "Escape") {
        setCommandOpen(false);
      }
    };
    window.addEventListener("keydown", handleGlobalKeys);
    return () => window.removeEventListener("keydown", handleGlobalKeys);
  }, [TAB_GROUPS, activeGroup, activeTab]);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const health = await apiGet("/health");
        setHealthData(health);
        setBackendStatus(health.status === "ok" ? "online" : "offline");
      } catch {
        setBackendStatus("offline");
      }

      try {
        const [propsData, rankingsData] = await Promise.all([
          apiGet("/properties?limit=50"),
          apiGet("/rankings/suburbs?limit=20"),
        ]);
        setProperties(propsData);
        setRankings(rankingsData);
      } catch (fetchError) {
        setError(fetchError.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const selectedProperty = useMemo(
    () => properties.find((p) => String(p.id) === selectedPropertyId),
    [properties, selectedPropertyId],
  );

  const compareProperty = useMemo(
    () => properties.find((p) => String(p.id) === comparePropertyId),
    [properties, comparePropertyId],
  );

  const confidenceTier = useMemo(() => {
    const confidence = valuation?.confidence_pct ?? 0;
    if (confidence >= 80) return "high";
    if (confidence >= 60) return "medium";
    return "low";
  }, [valuation]);

  const freshnessLabel = useMemo(() => (healthData?.freshness_status ? healthData.freshness_status : "unknown"), [healthData]);

  const premiumMockFeed = useMemo(
    () => ({
      news: [
        {
          id: "n1",
          headline: "Inner-ring Brisbane stock tightens as investor demand outpaces new supply",
          source: "Institutional Wire",
          time: "2h ago",
          impact: "high",
          summary: "Days-on-market compressed 11% week-over-week in monitored premium corridors.",
        },
        {
          id: "n2",
          headline: "Rental pressure index rises in high-yield corridors",
          source: "Yield Desk",
          time: "5h ago",
          impact: "medium",
          summary: "Leasing demand remains elevated while median asking rents continue repricing upward.",
        },
      ],
      monitor: [
        { id: "m1", title: "Risk Regime", value: "Moderate", detail: "Macro stress below trigger threshold", tone: "neutral" },
        { id: "m2", title: "Liquidity Pulse", value: "Strong", detail: "Turnover and inspection velocity accelerating", tone: "positive" },
        { id: "m3", title: "Funding Sensitivity", value: "Watch", detail: "+75 bps scenario reduces DSCR buffer", tone: "negative" },
      ],
      reportTemplates: [
        { id: "r1", name: "Investment Committee Memo", sections: 9, sla: "2 min export" },
        { id: "r2", name: "Bank Credit Pack", sections: 7, sla: "1 min export" },
      ],
    }),
    [],
  );

  const strategyPresets = useMemo(
    () => ({
      growth: { label: "Growth Focus", summary: "Prioritizes capital growth and trend acceleration.", weight: { growth: 0.5, yield: 0.2, liquidity: 0.3 } },
      cashflow: { label: "Cashflow Focus", summary: "Optimizes yield resilience and monthly surplus.", weight: { growth: 0.2, yield: 0.55, liquidity: 0.25 } },
      balanced: { label: "Balanced", summary: "Balances growth, yield, and market liquidity risk.", weight: { growth: 0.34, yield: 0.33, liquidity: 0.33 } },
    }),
    [],
  );

  const monthlyMortgage = useMemo(() => {
    const principal = calculator.price * (1 - calculator.depositPct / 100);
    const monthlyRate = calculator.interestPct / 100 / 12;
    const totalMonths = calculator.years * 12;
    if (monthlyRate <= 0 || totalMonths <= 0) return 0;
    const factor = Math.pow(1 + monthlyRate, totalMonths);
    return (principal * monthlyRate * factor) / (factor - 1);
  }, [calculator]);

  const monthlyCashflow = useMemo(() => {
    const rentMonthly = (calculator.weeklyRent * 52) / 12;
    return rentMonthly - monthlyMortgage - calculator.monthlyCosts;
  }, [calculator, monthlyMortgage]);

  const grossYieldPct = useMemo(() => {
    if (!calculator.price) return 0;
    const annualRent = calculator.weeklyRent * 52;
    return (annualRent / calculator.price) * 100;
  }, [calculator.price, calculator.weeklyRent]);

  const breakEvenWeeklyRent = useMemo(() => ((monthlyMortgage + calculator.monthlyCosts) * 12) / 52, [monthlyMortgage, calculator.monthlyCosts]);

  const watchlistSet = useMemo(() => new Set(watchlist.map((entry) => entry.id)), [watchlist]);

  const compAnchorProperty = useMemo(
    () => properties.find((p) => String(p.id) === compAnchorId) || selectedProperty || properties[0],
    [compAnchorId, properties, selectedProperty],
  );

  const compCandidates = useMemo(() => {
    if (!compAnchorProperty) return [];
    const list = properties
      .filter((p) => p.id !== compAnchorProperty.id)
      .map((p) => {
        const score =
          (p.suburb === compAnchorProperty.suburb ? 0.35 : 0) +
          (p.property_type === compAnchorProperty.property_type ? 0.25 : 0) +
          (1 - Math.min(Math.abs(p.bedrooms - compAnchorProperty.bedrooms) / 5, 1)) * 0.2 +
          (1 - Math.min(Math.abs(p.bathrooms - compAnchorProperty.bathrooms) / 4, 1)) * 0.2;
        return { property: p, similarity: Math.max(0, Math.min(1, score)) };
      })
      .sort((a, b) => b.similarity - a.similarity);
    return list.slice(0, 6);
  }, [properties, compAnchorProperty]);

  const compsPremiumRows = useMemo(
    () =>
      compCandidates.map((entry, index) => ({
        id: `comp-${entry.property.id}`,
        address: entry.property.address,
        suburb: entry.property.suburb,
        similarity: entry.similarity,
        distanceKm: (0.4 + index * 0.35).toFixed(1),
        recencyDays: 24 + index * 18,
        conditionAdjPct: (index % 2 === 0 ? -2.4 : 1.8).toFixed(1),
        confidence: Math.max(62, Math.round(entry.similarity * 100 - index * 3)),
      })),
    [compCandidates],
  );

  const rankedDeals = useMemo(() => {
    const preset = strategyPresets[strategyMode] ?? strategyPresets.balanced;
    return rankings
      .map((r, index) => {
        const growth = safeNumber(r.annual_growth_pct);
        const yieldPct = safeNumber(r.rental_yield_pct);
        const liquidity = Math.max(0, 10 - Math.min(10, growth));
        const score = growth * preset.weight.growth + yieldPct * 10 * preset.weight.yield + liquidity * preset.weight.liquidity;
        return {
          ...r,
          strategy_score: score,
          vacancy_pct: (1.8 + (index % 4) * 0.4).toFixed(1),
          liquidity_index: Math.max(0, Math.min(100, Math.round(score * 7.4))),
          institutional_demand: ["High", "Medium", "High", "Low"][index % 4],
        };
      })
      .sort((a, b) => b.strategy_score - a.strategy_score)
      .slice(0, 8);
  }, [rankings, strategyMode, strategyPresets]);

  const pipelineStages = ["Research", "Inspecting", "Negotiating", "Offer Made", "Won", "Lost"];

  const pipelineBuckets = useMemo(() => {
    const buckets = Object.fromEntries(pipelineStages.map((stage) => [stage, []]));
    watchlist.forEach((item) => {
      const stage = pipelineMap[item.id] || "Research";
      if (!buckets[stage]) buckets.Research.push(item);
      else buckets[stage].push(item);
    });
    return buckets;
  }, [watchlist, pipelineMap]);

  const dashboardKpis = useMemo(() => {
    const avgDealScore = rankedDeals.length ? rankedDeals.reduce((sum, row) => sum + row.strategy_score, 0) / rankedDeals.length : 0;
    const avgYield = rankedDeals.length ? rankedDeals.reduce((sum, row) => sum + safeNumber(row.rental_yield_pct), 0) / rankedDeals.length : 0;
    return { opportunities: rankedDeals.length, avgDealScore, avgYield, watchlistCount: watchlist.length };
  }, [rankedDeals, watchlist.length]);

  const urgencySignal = useMemo(() => {
    if (freshnessLabel === "degraded" || freshnessLabel === "stale") {
      return { tone: "warning", title: "Data freshness degraded", detail: "Hold fast decisions until pipeline catches up." };
    }
    if (confidenceTier === "low") {
      return { tone: "watch", title: "Confidence below target", detail: "Gather stronger comparables before committing." };
    }
    return { tone: "positive", title: "Signal regime favorable", detail: "Momentum and confidence are aligned for action." };
  }, [confidenceTier, freshnessLabel]);

  const narrativeBrief = useMemo(() => {
    if (!rankedDeals.length) {
      return "Loading market intelligence before generating a narrative brief.";
    }
    const topDeal = rankedDeals[0];
    return `${topDeal.suburb} is currently leading with ${topDeal.strategy_score.toFixed(2)} strategy score. Priority now is to validate downside risk while momentum remains favorable.`;
  }, [rankedDeals]);

  const recommendationCard = useMemo(() => {
    const score = valuation?.score ?? dashboardKpis.avgDealScore;
    if (score >= 7) {
      return {
        verdict: "Proceed with disciplined urgency",
        reason: "Signal quality and conviction are strong enough for near-term execution.",
        counter: "Counterpoint: run one more downside stress test before final offer terms.",
      };
    }
    if (score >= 5) {
      return {
        verdict: "Proceed selectively",
        reason: "Opportunity quality is balanced; execution timing and negotiation terms matter most.",
        counter: "Counterpoint: weak liquidity pockets may delay exits in a stress regime.",
      };
    }
    return {
      verdict: "Stay in discovery mode",
      reason: "Current inputs do not justify aggressive action under risk-adjusted mandate.",
      counter: "Counterpoint: strong local catalysts can still create tactical opportunities.",
    };
  }, [dashboardKpis.avgDealScore, valuation]);

  const marketPulse = useMemo(
    () => [
      { id: "pulse-score", label: "Conviction", value: dashboardKpis.avgDealScore.toFixed(2), delta: "+0.24" },
      { id: "pulse-yield", label: "Yield Edge", value: `${dashboardKpis.avgYield.toFixed(2)}%`, delta: "+0.31%" },
      { id: "pulse-fresh", label: "Freshness", value: freshnessLabel, delta: freshnessLabel === "fresh" ? "Live" : "Watch" },
      { id: "pulse-watch", label: "Tracked", value: String(watchlist.length), delta: `${watchlist.length > 0 ? "+" : ""}${watchlist.length}` },
    ],
    [dashboardKpis.avgDealScore, dashboardKpis.avgYield, freshnessLabel, watchlist.length],
  );

  const dataLineage = useMemo(
    () => [
      { id: "lineage-abs", label: "ABS", stamp: `${healthData?.freshness_minutes?.abs ?? "n/a"}m ago` },
      { id: "lineage-metrics", label: "Market Metrics", stamp: `${healthData?.freshness_minutes?.metrics ?? "n/a"}m ago` },
      { id: "lineage-model", label: "Model Regime", stamp: valuation?.deep_analysis?.market_regime ?? "not yet computed" },
    ],
    [healthData?.freshness_minutes?.abs, healthData?.freshness_minutes?.metrics, valuation?.deep_analysis?.market_regime],
  );

  const monitorAlerts = useMemo(
    () => [
      { id: "a1", title: "Liquidity alert eased in monitored metro corridor", level: "positive", time: "12m" },
      { id: "a2", title: "Macro stress index ticked above baseline watch-band", level: "neutral", time: "2h" },
      { id: "a3", title: "Funding sensitivity scenario hit warning threshold", level: "negative", time: "5h" },
    ],
    [],
  );

  const comparisonDelta = useMemo(() => {
    if (!valuation || !compareValuation) return null;
    return {
      scoreDelta: valuation.score - compareValuation.score,
      midDelta: valuation.mid_estimate - compareValuation.mid_estimate,
      confidenceDelta: valuation.confidence_pct - compareValuation.confidence_pct,
    };
  }, [valuation, compareValuation]);

  function toggleWatchlist(property) {
    if (!property) return;
    const exists = watchlistSet.has(property.id);
    const next = exists
      ? watchlist.filter((item) => item.id !== property.id)
      : [...watchlist, { id: property.id, address: property.address, suburb: property.suburb, state: property.state, savedAt: new Date().toISOString() }];
    setWatchlist(next);
    localStorage.setItem(STORAGE_KEYS.watchlist, JSON.stringify(next));
    if (exists) {
      const nextPipeline = { ...pipelineMap };
      delete nextPipeline[property.id];
      setPipelineMap(nextPipeline);
      localStorage.setItem(STORAGE_KEYS.pipeline, JSON.stringify(nextPipeline));
    }
  }

  function setPipelineStage(propertyId, stage) {
    const next = { ...pipelineMap, [propertyId]: stage };
    setPipelineMap(next);
    localStorage.setItem(STORAGE_KEYS.pipeline, JSON.stringify(next));
  }

  function saveCurrentReport() {
    if (!valuation || !selectedProperty) return;
    const report = {
      id: `${Date.now()}-${selectedProperty.id}`,
      propertyId: selectedProperty.id,
      address: selectedProperty.address,
      suburb: selectedProperty.suburb,
      score: valuation.score,
      confidence: valuation.confidence_pct,
      createdAt: new Date().toISOString(),
      summary: valuation.reasons.slice(0, 3),
    };
    const next = [report, ...savedReports].slice(0, 25);
    setSavedReports(next);
    localStorage.setItem(STORAGE_KEYS.reports, JSON.stringify(next));
    setActiveTab("reports");
  }

  function applyStrategy(mode) {
    setStrategyMode(mode);
    localStorage.setItem(STORAGE_KEYS.strategy, mode);
  }

  async function runSingleValuation(propertyId) {
    if (!propertyId) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost("/valuation", { property_id: Number(propertyId) });
      setValuation(data);
      setResearchPack(null);
      setPortfolioRisk(null);
      setSelectedPropertyId(String(propertyId));
      setActiveTab("briefs");
    } catch (postError) {
      setError(postError.message);
    } finally {
      setLoading(false);
    }
  }

  async function runComparison() {
    if (!selectedPropertyId) return;
    setLoading(true);
    setError("");
    try {
      const requests = [apiPost("/valuation", { property_id: Number(selectedPropertyId) })];
      if (comparePropertyId && comparePropertyId !== selectedPropertyId) {
        requests.push(apiPost("/valuation", { property_id: Number(comparePropertyId) }));
      }
      const [primary, secondary] = await Promise.all(requests);
      setValuation(primary);
      setCompareValuation(secondary || null);
      setResearchPack(null);
      setPortfolioRisk(null);
      setActiveTab("comparison");
    } catch (postError) {
      setCompareValuation(null);
      setError(postError.message);
    } finally {
      setLoading(false);
    }
  }

  async function runResearchPack(propertyId) {
    if (!propertyId) return;
    setResearchLoading(true);
    setError("");
    try {
      const grossAnnualRent = (calculator.weeklyRent * 52) || 1;
      const annualCosts = calculator.monthlyCosts * 12;
      const expenseRatioPct = Math.max(5, Math.min(70, (annualCosts / grossAnnualRent) * 100));
      const data = await apiPost("/valuation/research", {
        property_id: Number(propertyId),
        assumptions: {
          lvr_pct: Math.max(30, Math.min(95, 100 - calculator.depositPct)),
          interest_rate_pct: Math.max(0.1, Math.min(20, calculator.interestPct)),
          loan_years: Math.max(5, Math.min(40, calculator.years)),
          expense_ratio_pct: Number(expenseRatioPct.toFixed(2)),
          vacancy_weeks: 2,
          exit_cost_pct: 2.5,
          gross_income_annual: 210000,
          other_debt_annual: 18000,
          tax_rate_pct: 37,
          depreciation_annual: 6000,
          hold_years: 5,
        },
      });
      setResearchPack(data);
    } catch (postError) {
      setError(postError.message);
    } finally {
      setResearchLoading(false);
    }
  }

  async function runPortfolioRiskSimulation() {
    const sourceRows = watchlist.length
      ? watchlist
          .map((item) => properties.find((property) => property.id === item.id))
          .filter(Boolean)
      : properties.slice(0, 6);
    if (!sourceRows.length) return;

    setPortfolioRiskLoading(true);
    setError("");
    try {
      const rows = sourceRows.map((property, index) => {
        const assumedValue = valuation?.property_id === property.id ? valuation.mid_estimate : calculator.price * (0.78 + index * 0.03);
        const annualRent = (assumedValue * (grossYieldPct / 100 || 0.045));
        return {
          purchase_price: Math.max(350000, Number(assumedValue.toFixed(2))),
          lvr_pct: Math.max(45, Math.min(90, 100 - calculator.depositPct + (index % 3))),
          interest_rate_pct: Math.max(0.1, Math.min(20, calculator.interestPct + ((index % 3) - 1) * 0.2)),
          loan_years: Math.max(5, Math.min(40, calculator.years)),
          annual_rent: Number(annualRent.toFixed(2)),
          annual_expenses: Number((annualRent * 0.24).toFixed(2)),
        };
      });

      const result = await apiPost("/valuation/portfolio-risk", { items: rows });
      setPortfolioRisk(result);
    } catch (postError) {
      setError(postError.message);
    } finally {
      setPortfolioRiskLoading(false);
    }
  }

  const scoreTone = useMemo(() => {
    if (!valuation) return "score-neutral";
    if (valuation.score >= 7) return "score-strong";
    if (valuation.score >= 5) return "score-balanced";
    return "score-watch";
  }, [valuation]);

  const topProperties = useMemo(() => properties.slice(0, 8), [properties]);

  const newsItems = useMemo(() => {
    const topSuburbs = rankings.slice(0, 3);
    const generated = topSuburbs.map((row, index) => ({
      id: `suburb-${row.postcode}-${index}`,
      title: `${row.suburb} momentum remains strong with ${row.annual_growth_pct.toFixed(1)}% annual growth`,
      source: "SignalEstate Insights",
      category: "Suburb Trend",
      summary: `Median sits near ${formatMoney(row.median_price)} and yield is ${row.rental_yield_pct.toFixed(1)}%. Investors should watch supply and days-on-market in this pocket.`,
    }));
    return [...premiumMockFeed.news, ...generated];
  }, [rankings, premiumMockFeed.news]);

  const activeGroupTabs = useMemo(() => {
    const group = TAB_GROUPS.find((entry) => entry.id === activeGroup) || TAB_GROUPS[0];
    return group.tabs;
  }, [TAB_GROUPS, activeGroup]);

  const tabLookup = useMemo(() => {
    const map = {};
    TAB_GROUPS.forEach((group) => {
      group.tabs.forEach((tab) => {
        map[tab.id] = { ...tab, groupId: group.id, groupLabel: group.label };
      });
    });
    return map;
  }, [TAB_GROUPS]);

  const commandItems = useMemo(() => {
    const normalized = commandQuery.trim().toLowerCase();
    const allTabs = TAB_GROUPS.flatMap((group) =>
      group.tabs.map((tab) => ({
        ...tab,
        groupId: group.id,
        groupLabel: group.label,
      })),
    );
    if (!normalized) return allTabs;
    return allTabs.filter((item) => {
      return (
        item.label.toLowerCase().includes(normalized) ||
        item.groupLabel.toLowerCase().includes(normalized) ||
        item.icon.toLowerCase().includes(normalized)
      );
    });
  }, [TAB_GROUPS, commandQuery]);

  const tabMeta = useMemo(
    () => ({
      trending: {
        subtitle: "Live opportunities",
        metric: `${topProperties.length}`,
        tone: topProperties.length >= 6 ? "strong" : "watch",
      },
      deals: {
        subtitle: "Ranked by strategy",
        metric: rankedDeals.length ? rankedDeals[0].strategy_score.toFixed(2) : "--",
        tone: rankedDeals.length >= 5 ? "strong" : "watch",
      },
      news: {
        subtitle: "Market intelligence",
        metric: `${newsItems.length}`,
        tone: newsItems.length >= 4 ? "strong" : "neutral",
      },
      comps: {
        subtitle: "Comparable depth",
        metric: `${compsPremiumRows.length}`,
        tone: compsPremiumRows.length >= 3 ? "strong" : "watch",
      },
      comparison: {
        subtitle: "Side-by-side underwriting",
        metric: comparisonDelta ? comparisonDelta.scoreDelta.toFixed(2) : "--",
        tone: comparisonDelta ? "strong" : "neutral",
      },
      calculators: {
        subtitle: "Cashflow stress tests",
        metric: `${grossYieldPct.toFixed(1)}%`,
        tone: grossYieldPct >= 4.5 ? "strong" : "watch",
      },
      monitor: {
        subtitle: "System healthboard",
        metric: freshnessLabel,
        tone: freshnessLabel === "fresh" ? "strong" : "watch",
      },
      strategy: {
        subtitle: "Mandate controls",
        metric: strategyPresets[strategyMode]?.label || "Balanced",
        tone: "neutral",
      },
      briefs: {
        subtitle: "Decision memo",
        metric: valuation ? valuation.score.toFixed(2) : "--",
        tone: valuation?.score >= 7 ? "strong" : valuation ? "neutral" : "watch",
      },
      pipeline: {
        subtitle: "Acquisition flow",
        metric: `${watchlist.length}`,
        tone: watchlist.length ? "strong" : "watch",
      },
      watchlist: {
        subtitle: "Tracked targets",
        metric: `${watchlist.length}`,
        tone: watchlist.length ? "strong" : "watch",
      },
      reports: {
        subtitle: "Saved outputs",
        metric: `${savedReports.length}`,
        tone: savedReports.length ? "strong" : "neutral",
      },
    }),
    [
      comparisonDelta,
      compsPremiumRows.length,
      freshnessLabel,
      grossYieldPct,
      newsItems.length,
      rankedDeals,
      savedReports.length,
      strategyMode,
      strategyPresets,
      topProperties.length,
      valuation,
      watchlist.length,
    ],
  );

  const groupMeta = useMemo(() => {
    return TAB_GROUPS.map((group) => {
      const tabsWithMeta = group.tabs.map((tab) => ({ id: tab.id, meta: tabMeta[tab.id] }));
      const strongCount = tabsWithMeta.filter((entry) => entry.meta?.tone === "strong").length;
      const watchCount = tabsWithMeta.filter((entry) => entry.meta?.tone === "watch").length;
      const summary =
        strongCount > 0
          ? `${strongCount} high-signal workspaces`
          : watchCount > 0
            ? `${watchCount} workspaces need attention`
            : "stable operational posture";
      return {
        id: group.id,
        tabCount: group.tabs.length,
        strongCount,
        watchCount,
        summary,
      };
    });
  }, [TAB_GROUPS, tabMeta]);

  const activeTabMeta = tabMeta[activeTab] || { subtitle: "", metric: "--", tone: "neutral" };
  const activeGroupMeta = groupMeta.find((entry) => entry.id === activeGroup);

  const quickActions = [
    {
      id: "qa-open-comparison",
      label: "Open Comparison Workspace",
      detail: "Jump to analysis comparison tools",
      icon: "CM",
      run: () => selectTab("analysis", "comparison"),
    },
    {
      id: "qa-open-reports",
      label: "Open Reports Vault",
      detail: "View saved briefs and export templates",
      icon: "RP",
      run: () => selectTab("execution", "reports"),
    },
    {
      id: "qa-open-pipeline",
      label: "Open Pipeline Board",
      detail: "Track acquisition workflow stages",
      icon: "PL",
      run: () => selectTab("execution", "pipeline"),
    },
    {
      id: "qa-analyze-selected",
      label: "Analyze Selected Property",
      detail: selectedPropertyId ? `Run valuation on #${selectedPropertyId}` : "Select a property first in Comparison",
      icon: "AN",
      run: () => {
        if (selectedPropertyId) {
          runSingleValuation(selectedPropertyId);
          setCommandOpen(false);
        } else {
          selectTab("analysis", "comparison");
        }
      },
    },
  ];

  useEffect(() => {
    if (commandFocusIndex >= commandItems.length) {
      setCommandFocusIndex(0);
    }
  }, [commandFocusIndex, commandItems.length]);

  function selectTab(groupId, tabId) {
    setActiveGroup(groupId);
    setActiveTab(tabId);
    setCommandOpen(false);
  }

  function selectGroup(groupId) {
    const nextGroup = TAB_GROUPS.find((group) => group.id === groupId);
    if (!nextGroup) return;
    setActiveGroup(groupId);
    const hasActiveInGroup = nextGroup.tabs.some((tab) => tab.id === activeTab);
    if (!hasActiveInGroup) {
      setActiveTab(nextGroup.tabs[0].id);
    }
  }

  function onCommandKeyDown(event) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setCommandFocusIndex((prev) => (prev + 1) % Math.max(commandItems.length, 1));
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setCommandFocusIndex((prev) => (prev - 1 + Math.max(commandItems.length, 1)) % Math.max(commandItems.length, 1));
    }
    if (event.key === "Enter" && commandItems[commandFocusIndex]) {
      const item = commandItems[commandFocusIndex];
      selectTab(item.groupId, item.id);
    }
  }

  function createArtifact(type) {
    const item = {
      id: `${Date.now()}-${type}`,
      type,
      title: `${type} • ${new Date().toLocaleDateString()}`,
      note: selectedProperty?.address || "Portfolio-level output",
      createdAt: new Date().toISOString(),
    };
    const next = [item, ...artifacts].slice(0, 10);
    setArtifacts(next);
    localStorage.setItem(STORAGE_KEYS.artifacts, JSON.stringify(next));
    setActiveTab("reports");
  }

  function applyThemePreset(preset) {
    setThemePreset(preset);
    localStorage.setItem(STORAGE_KEYS.theme, preset);
  }

  return (
    <div className="app-shell futuristic-ui">
      <header className="app-topbar">
        <a href="/" className="brand-wordmark">
          SignalEstate
        </a>
        <div className="app-topbar-actions">
          <div className="topbar-status-cluster">
            <span className={`backend-dot backend-${backendStatus}`}>
              Backend {backendStatus === "checking" ? "checking" : backendStatus}
            </span>
            <span className="topbar-mini-label">Workspace</span>
          </div>
          <div className="topbar-display-cluster">
            <div className="theme-switcher" role="group" aria-label="Theme presets">
              {THEME_PRESETS.map((theme) => (
                <button
                  key={theme.id}
                  className={themePreset === theme.id ? "theme-chip active" : "theme-chip"}
                  onClick={() => applyThemePreset(theme.id)}
                >
                  {theme.label}
                </button>
              ))}
            </div>
            <button
              className={liquidGlass ? "glass-toggle-btn active" : "glass-toggle-btn"}
              onClick={() => setLiquidGlass((prev) => !prev)}
              aria-pressed={liquidGlass}
            >
              {liquidGlass ? "Glass On" : "Glass Off"}
            </button>
          </div>
          <div className="topbar-link-row">
            <a href="/guide.html" target="_blank" rel="noreferrer">
              Guide
            </a>
            <a href="/">Landing</a>
          </div>
        </div>
      </header>

      <section className="panel narrative-hero">
        <div className="narrative-hero-left">
          <p className="eyebrow">Market Storyline</p>
          <h2>{recommendationCard.verdict}</h2>
          <p>{narrativeBrief}</p>
          <div className={`urgency-chip urgency-${urgencySignal.tone}`}>
            <strong>{urgencySignal.title}</strong>
            <span>{urgencySignal.detail}</span>
          </div>
        </div>
        <div className="narrative-hero-right">
          <article className="recommendation-card">
            <h3>Primary Recommendation</h3>
            <p>{recommendationCard.reason}</p>
            <small>{recommendationCard.counter}</small>
          </article>
          <div className="pulse-grid">
            {marketPulse.map((item) => (
              <article key={item.id} className="pulse-card">
                <span>{item.label}</span>
                <strong>{item.value}</strong>
                <small>{item.delta}</small>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="panel executive-strip">
        <div className="executive-kpi-grid">
          <NumberPill label="Active Opportunities" value={dashboardKpis.opportunities} />
          <NumberPill label="Avg Deal Score" value={dashboardKpis.avgDealScore.toFixed(2)} />
          <NumberPill label="Avg Yield" value={`${dashboardKpis.avgYield.toFixed(2)}%`} />
          <NumberPill label="Watchlist" value={dashboardKpis.watchlistCount} />
        </div>
      </section>

      <section className="panel">
        <div className="tab-group-row" role="tablist" aria-label="Tab groups" ref={groupRowRef}>
          {TAB_GROUPS.map((group) => (
            <button
              key={group.id}
              ref={(node) => {
                groupButtonRefs.current[group.id] = node;
              }}
              className={activeGroup === group.id ? "tab-group-btn active" : "tab-group-btn"}
              onClick={() => selectGroup(group.id)}
              role="tab"
              aria-selected={activeGroup === group.id}
              aria-controls={`panel-${group.tabs[0].id}`}
              title="Alt+G cycles group"
            >
              <span className="tab-group-btn-label">{group.label}</span>
              <span className="tab-group-meta">
                {groupMeta.find((item) => item.id === group.id)?.tabCount || group.tabs.length} tabs
              </span>
            </button>
          ))}
        </div>

        <div className="spa-tab-row" role="tablist" aria-label="Workspace tabs" ref={tabRowRef}>
          <span className="spa-tab-indicator" style={{ left: tabIndicator.left, width: tabIndicator.width }} aria-hidden="true" />
          {activeGroupTabs.map((tab) => {
            const groupForTab = TAB_GROUPS.find((entry) => entry.tabs.some((entryTab) => entryTab.id === tab.id));
            return (
              <button
                key={tab.id}
                ref={(node) => {
                  tabButtonRefs.current[tab.id] = node;
                }}
                className={activeTab === tab.id ? "spa-tab active" : "spa-tab"}
                onClick={() => selectTab(groupForTab?.id || activeGroup, tab.id)}
                role="tab"
                aria-selected={activeTab === tab.id}
                aria-controls={`panel-${tab.id}`}
                title={`Alt+${activeGroupTabs.findIndex((item) => item.id === tab.id) + 1} to open`}
              >
                <span className="spa-tab-icon" aria-hidden="true">{tab.icon}</span>
                <span className="spa-tab-main">
                  <span className="spa-tab-title">{tab.label}</span>
                  <span className="spa-tab-subtitle">{tabMeta[tab.id]?.subtitle || "Workspace"}</span>
                </span>
                <span className={`spa-tab-metric metric-${tabMeta[tab.id]?.tone || "neutral"}`}>
                  {tabMeta[tab.id]?.metric || "--"}
                </span>
              </button>
            );
          })}
        </div>

        <div className="tab-intel-row" aria-live="polite">
          <article className="tab-intel-card">
            <span>Active Workspace</span>
            <strong>{tabLookup[activeTab]?.label || "Overview"}</strong>
            <p>{activeTabMeta.subtitle}</p>
          </article>
          <article className="tab-intel-card">
            <span>Current Signal</span>
            <strong>{activeTabMeta.metric}</strong>
            <p>{activeGroupMeta?.summary || "Monitoring operational indicators."}</p>
          </article>
          <article className="tab-intel-card">
            <span>Power Shortcuts</span>
            <strong>Ctrl+K / Alt+1-9 / Alt+Arrows</strong>
            <p>Command palette, direct tab jump, and next/previous navigation for faster workflows.</p>
          </article>
        </div>

        <div className="recent-tabs-row" aria-label="Recent tabs">
          <span className="recent-tabs-label">Recent</span>
          <div className="recent-tabs-chips">
            {recentTabs
              .filter((tabId) => tabId !== activeTab)
              .map((tabId) => {
                const tab = tabLookup[tabId];
                if (!tab) return null;
                return (
                  <button key={tab.id} className="recent-tab-chip" onClick={() => selectTab(tab.groupId, tab.id)}>
                    <span className="recent-tab-chip-icon" aria-hidden="true">{tab.icon}</span>
                    <span>{tab.label}</span>
                  </button>
                );
              })}
          </div>
        </div>
      </section>

      <section className="panel lineage-strip-panel">
        <div className="lineage-strip">
          {dataLineage.map((item) => (
            <div key={item.id} className="lineage-pill">
              <span>{item.label}</span>
              <strong>{item.stamp}</strong>
            </div>
          ))}
        </div>
      </section>

      {commandOpen && (
        <div className="command-palette-overlay" onClick={() => setCommandOpen(false)}>
          <section className="command-palette" onClick={(event) => event.stopPropagation()}>
            <div className="command-head">
              <strong>Jump To Tab</strong>
              <small>Ctrl+K</small>
            </div>
            <input
              autoFocus
              type="text"
              className="command-input"
              placeholder="Search tabs or groups..."
              value={commandQuery}
              onChange={(event) => {
                setCommandQuery(event.target.value);
                setCommandFocusIndex(0);
              }}
              onKeyDown={onCommandKeyDown}
            />

            <div className="command-quick-actions">
              <p>Quick Actions</p>
              <div className="command-quick-grid">
                {quickActions.map((action) => (
                  <button key={action.id} className="command-quick-item" onClick={action.run}>
                    <span className="command-item-icon" aria-hidden="true">{action.icon}</span>
                    <span>
                      <strong>{action.label}</strong>
                      <small>{action.detail}</small>
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <ul className="command-results">
              {commandItems.length === 0 ? (
                <li className="command-empty">No matching tabs</li>
              ) : (
                commandItems.map((item, index) => (
                  <li key={`${item.groupId}-${item.id}`}>
                    <button
                      className={index === commandFocusIndex ? "command-item active" : "command-item"}
                      onMouseEnter={() => setCommandFocusIndex(index)}
                      onClick={() => selectTab(item.groupId, item.id)}
                    >
                      <span className="command-item-icon" aria-hidden="true">{item.icon}</span>
                      <span>{item.label}</span>
                      <small>{item.groupLabel}</small>
                    </button>
                  </li>
                ))
              )}
            </ul>
          </section>
        </div>
      )}

      {error && <section className="panel error">{error}</section>}

      {activeTab === "trending" && (
        <section id="panel-trending" className="panel tab-panel">
          <h2>Trending Properties</h2>
          <p className="muted">Executive shortlist of active targets with one-click analysis actions.</p>
          <div className="spotlight-banner">
            <strong>Today&apos;s positioning:</strong> Momentum still favors yield-supported suburbs, while funding sensitivity remains the primary risk control.
          </div>
          {loading && topProperties.length === 0 ? (
            <LoadingSkeleton lines={6} />
          ) : (
            <div className="spa-card-grid">
              {topProperties.map((property) => (
                <article key={property.id} className="spa-property-card">
                  <h3>{property.address}</h3>
                  <p className="muted">
                    {property.suburb}, {property.state} {property.postcode}
                  </p>
                  <div className="pill-inline-wrap">
                    <span>{property.property_type}</span>
                    <span>{property.bedrooms} bd</span>
                    <span>{property.bathrooms} ba</span>
                    <span>{property.carspaces} car</span>
                  </div>
                  <p className="card-micro-insight">Signal: add this to watchlist if yield stays above 4.8% and liquidity remains stable.</p>
                  <div className="card-actions">
                    <button className="subtle-btn" onClick={() => toggleWatchlist(property)}>
                      {watchlistSet.has(property.id) ? "Unwatch" : "Watch"}
                    </button>
                    <button onClick={() => runSingleValuation(property.id)}>Analyze</button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      {activeTab === "deals" && (
        <section id="panel-deals" className="panel tab-panel">
          <h2>Deals Desk</h2>
          <p className="muted">Institutional ranking board tuned to your selected strategy profile.</p>
          <div className="context-grid">
            <div className="context-card">
              <h3>Desk Commentary</h3>
              <p>High-conviction entries show stronger yield-resilience and liquidity depth than the broader sample.</p>
            </div>
            <div className="context-card">
              <h3>Mandate</h3>
              <p>{strategyPresets[strategyMode].label}: {strategyPresets[strategyMode].summary}</p>
            </div>
          </div>
          <div className="deals-table-wrap">
            <table className="deals-table">
              <thead>
                <tr>
                  <th>Suburb</th>
                  <th>Strategy Score</th>
                  <th>Median</th>
                  <th>Growth</th>
                  <th>Yield</th>
                  <th>Vacancy</th>
                  <th>Liquidity</th>
                  <th>Demand</th>
                </tr>
              </thead>
              <tbody>
                {rankedDeals.map((deal) => (
                  <tr key={`${deal.postcode}-${deal.suburb}`}>
                    <td>{deal.suburb}, {deal.state}</td>
                    <td>{deal.strategy_score.toFixed(2)}</td>
                    <td>{formatMoney(deal.median_price)}</td>
                    <td>{deal.annual_growth_pct.toFixed(1)}%</td>
                    <td>{deal.rental_yield_pct.toFixed(1)}%</td>
                    <td>{deal.vacancy_pct}%</td>
                    <td>{deal.liquidity_index}</td>
                    <td>{deal.institutional_demand}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {activeTab === "news" && (
        <section id="panel-news" className="panel tab-panel">
          <h2>Property News</h2>
          <p className="muted">Signal feed combining suburb momentum, macro watch, and data quality insights.</p>
          <div className="news-brief-grid">
            <div className="context-card">
              <h3>Coverage Window</h3>
              <p>Rolling 24h blend from institutional wires, macro updates, and system intelligence.</p>
            </div>
            <div className="context-card">
              <h3>Signal Quality</h3>
              <p>Priority-weighted by relevance to investor cashflow, liquidity, and downside risk controls.</p>
            </div>
          </div>
          <div className="news-grid">
            {newsItems.map((item) => (
              <article key={item.id} className="news-card">
                <div className="news-meta">
                  <span>{item.category || "Market"}</span>
                  <small>
                    {item.source}
                    {item.time ? ` • ${item.time}` : ""}
                  </small>
                </div>
                <h3>{item.title || item.headline}</h3>
                <p>{item.summary}</p>
                {item.impact && <em className={`impact-tag impact-${item.impact}`}>Impact: {item.impact}</em>}
              </article>
            ))}
          </div>
        </section>
      )}

      {activeTab === "comps" && (
        <section id="panel-comps" className="panel tab-panel">
          <h2>Comparable Sales Lens</h2>
          <p className="muted">Review likely comparables ranked by structural similarity and location context.</p>
          <div className="command-row">
            <select value={compAnchorId} onChange={(e) => setCompAnchorId(e.target.value)}>
              <option value="">Anchor property...</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>
                  #{p.id} {p.address} - {p.suburb}
                </option>
              ))}
            </select>
            {compAnchorProperty && (
              <button onClick={() => runSingleValuation(compAnchorProperty.id)} disabled={loading}>
                Analyze Anchor
              </button>
            )}
          </div>
          {compCandidates.length === 0 ? (
            <p className="muted">Not enough properties loaded to build comparable sets.</p>
          ) : (
            <>
              <div className="context-grid">
                <div className="context-card">
                  <h3>Anchor Property</h3>
                  <p>{compAnchorProperty?.address || "Not selected"}</p>
                </div>
                <div className="context-card">
                  <h3>Comparable Depth</h3>
                  <p>{compsPremiumRows.length} high-similarity assets with adjustment diagnostics.</p>
                </div>
              </div>
              <div className="deals-table-wrap">
                <table className="deals-table comps-table">
                  <thead>
                    <tr>
                      <th>Address</th>
                      <th>Similarity</th>
                      <th>Distance</th>
                      <th>Recency</th>
                      <th>Condition Adj</th>
                      <th>Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compsPremiumRows.map((row) => (
                      <tr key={row.id}>
                        <td>
                          {row.address}
                          <div className="muted">{row.suburb}</div>
                        </td>
                        <td>{(row.similarity * 100).toFixed(0)}%</td>
                        <td>{row.distanceKm} km</td>
                        <td>{row.recencyDays} days</td>
                        <td>{row.conditionAdjPct}%</td>
                        <td>{row.confidence}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      )}

      {activeTab === "comparison" && (
        <section id="panel-comparison" className="panel tab-panel">
          <h2>Property Comparison</h2>
          <div className="command-row">
            <select value={selectedPropertyId} onChange={(e) => setSelectedPropertyId(e.target.value)}>
              <option value="">Primary property...</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>
                  #{p.id} {p.address} - {p.suburb}
                </option>
              ))}
            </select>
            <select value={comparePropertyId} onChange={(e) => setComparePropertyId(e.target.value)}>
              <option value="">Comparison property...</option>
              {properties
                .filter((p) => String(p.id) !== selectedPropertyId)
                .map((p) => (
                  <option key={p.id} value={p.id}>
                    #{p.id} {p.address} - {p.suburb}
                  </option>
                ))}
            </select>
            <button onClick={runComparison} disabled={!selectedPropertyId || loading}>
              {loading ? "Running..." : "Run Comparison"}
            </button>
          </div>
          {valuation && selectedProperty ? (
            <>
              <div className="compare-grid">
                <div className="compare-card">
                  <h3>{selectedProperty.address}</h3>
                  <p className="muted">{selectedProperty.suburb}</p>
                  <p>
                    <strong>Score:</strong> {valuation.score.toFixed(2)}
                  </p>
                  <p>
                    <strong>Mid:</strong> {formatMoney(valuation.mid_estimate)}
                  </p>
                  <p>
                    <strong>Confidence:</strong> {valuation.confidence_pct}%
                  </p>
                </div>
                <div className="compare-card">
                  {compareValuation && compareProperty ? (
                    <>
                      <h3>{compareProperty.address}</h3>
                      <p className="muted">{compareProperty.suburb}</p>
                      <p>
                        <strong>Score:</strong> {compareValuation.score.toFixed(2)}
                      </p>
                      <p>
                        <strong>Mid:</strong> {formatMoney(compareValuation.mid_estimate)}
                      </p>
                      <p>
                        <strong>Confidence:</strong> {compareValuation.confidence_pct}%
                      </p>
                    </>
                  ) : (
                    <p className="muted">Select a second property and run comparison to populate this panel.</p>
                  )}
                </div>
              </div>
              {comparisonDelta && (
                <div className="comparison-delta-card">
                  <h3>Decision Delta</h3>
                  <div className="executive-kpi-grid compact">
                    <NumberPill label="Score Delta" value={comparisonDelta.scoreDelta.toFixed(2)} />
                    <NumberPill label="Mid Value Delta" value={formatMoney(comparisonDelta.midDelta)} />
                    <NumberPill label="Confidence Delta" value={`${comparisonDelta.confidenceDelta.toFixed(1)}%`} />
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="muted">Select properties and run comparison.</p>
          )}
        </section>
      )}

      {activeTab === "calculators" && (
        <section id="panel-calculators" className="panel tab-panel">
          <h2>Investment Calculators</h2>
          <p className="muted">Formal underwriting calculator for debt service and monthly cashflow stress testing.</p>
          <div className="calc-grid">
            <label>
              Property Price
              <input type="number" value={calculator.price} onChange={(e) => setCalculator((prev) => ({ ...prev, price: Number(e.target.value || 0) }))} />
            </label>
            <label>
              Deposit %
              <input type="number" value={calculator.depositPct} onChange={(e) => setCalculator((prev) => ({ ...prev, depositPct: Number(e.target.value || 0) }))} />
            </label>
            <label>
              Interest %
              <input type="number" step="0.1" value={calculator.interestPct} onChange={(e) => setCalculator((prev) => ({ ...prev, interestPct: Number(e.target.value || 0) }))} />
            </label>
            <label>
              Loan Years
              <input type="number" value={calculator.years} onChange={(e) => setCalculator((prev) => ({ ...prev, years: Number(e.target.value || 0) }))} />
            </label>
            <label>
              Weekly Rent
              <input type="number" value={calculator.weeklyRent} onChange={(e) => setCalculator((prev) => ({ ...prev, weeklyRent: Number(e.target.value || 0) }))} />
            </label>
            <label>
              Monthly Costs
              <input type="number" value={calculator.monthlyCosts} onChange={(e) => setCalculator((prev) => ({ ...prev, monthlyCosts: Number(e.target.value || 0) }))} />
            </label>
          </div>
          <div className="calc-results">
            <NumberPill label="Estimated Monthly Mortgage" value={formatMoney(monthlyMortgage)} />
            <NumberPill label="Estimated Monthly Cashflow" value={formatMoney(monthlyCashflow)} />
            <NumberPill label="Gross Yield" value={`${grossYieldPct.toFixed(2)}%`} />
            <NumberPill label="Break-Even Weekly Rent" value={formatMoney(breakEvenWeeklyRent)} />
          </div>
        </section>
      )}

      {activeTab === "pipeline" && (
        <section id="panel-pipeline" className="panel tab-panel">
          <h2>Acquisition Pipeline</h2>
          <p className="muted">Track each watched opportunity from research to win/loss outcome.</p>
          <div className="pipeline-grid">
            {pipelineStages.map((stage) => (
              <div key={stage} className="pipeline-column">
                <h3>
                  {stage} <span>{pipelineBuckets[stage]?.length || 0}</span>
                </h3>
                {(pipelineBuckets[stage] || []).length === 0 ? (
                  <p className="muted">No items</p>
                ) : (
                  <ul className="pipeline-list">
                    {pipelineBuckets[stage].map((item) => (
                      <li key={`${stage}-${item.id}`}>
                        <strong>{item.address}</strong>
                        <small>
                          {item.suburb}, {item.state}
                        </small>
                        <select value={pipelineMap[item.id] || "Research"} onChange={(e) => setPipelineStage(item.id, e.target.value)}>
                          {pipelineStages.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {activeTab === "monitor" && (
        <section id="panel-monitor" className="panel tab-panel">
          <h2>Monitor</h2>
          <p className="muted">Operational confidence, model readiness, and data freshness healthboard.</p>
          <div className="trust-grid">
            <div className={`trust-chip trust-${freshnessLabel}`}>Freshness: {freshnessLabel}</div>
            <div className={`trust-chip trust-${confidenceTier}`}>
              Confidence: {valuation ? `${valuation.confidence_pct}%` : "No brief"}
            </div>
            <div className="trust-chip trust-neutral">Backend: {backendStatus}</div>
          </div>
          <ul className="detail-list">
            <li>ABS freshness minutes: {healthData?.freshness_minutes?.abs ?? "n/a"}</li>
            <li>Metrics freshness minutes: {healthData?.freshness_minutes?.metrics ?? "n/a"}</li>
            <li>Last model regime: {valuation?.deep_analysis?.market_regime ?? "n/a"}</li>
          </ul>
          <div className="monitor-feed-grid">
            {premiumMockFeed.monitor.map((item) => (
              <article key={item.id} className="monitor-feed-card">
                <div>
                  <h3>{item.title}</h3>
                  <p className="muted">{item.detail}</p>
                </div>
                <span className={`impact-tag impact-${item.tone}`}>{item.value}</span>
              </article>
            ))}
          </div>
          <div className="alert-timeline">
            <h3>Alert Timeline</h3>
            <ul>
              {monitorAlerts.map((alert) => (
                <li key={alert.id}>
                  <span className={`impact-tag impact-${alert.level}`}>{alert.time}</span>
                  <p>{alert.title}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}

      {activeTab === "watchlist" && (
        <section id="panel-watchlist" className="panel tab-panel">
          <h2>Watchlist</h2>
          {watchlist.length === 0 ? (
            <p className="muted">No watchlist items yet. Add from Trending.</p>
          ) : (
            <ul className="watchlist-list">
              {watchlist.map((item) => (
                <li key={item.id}>
                  <div>
                    <strong>{item.address}</strong>
                    <small>
                      {item.suburb}, {item.state}
                    </small>
                  </div>
                  <div className="card-actions">
                    <button className="subtle-btn" onClick={() => toggleWatchlist(item)}>
                      Remove
                    </button>
                    <button onClick={() => runSingleValuation(item.id)}>Analyze</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {activeTab === "strategy" && (
        <section id="panel-strategy" className="panel tab-panel">
          <h2>Strategy Profiles</h2>
          <p className="muted">Switch investment mandate and instantly re-rank market opportunities.</p>
          <div className="strategy-grid">
            {Object.entries(strategyPresets).map(([key, preset]) => (
              <article key={key} className={strategyMode === key ? "strategy-card active" : "strategy-card"}>
                <h3>{preset.label}</h3>
                <p>{preset.summary}</p>
                <ul className="detail-list">
                  <li>Growth weight: {(preset.weight.growth * 100).toFixed(0)}%</li>
                  <li>Yield weight: {(preset.weight.yield * 100).toFixed(0)}%</li>
                  <li>Liquidity weight: {(preset.weight.liquidity * 100).toFixed(0)}%</li>
                </ul>
                <button onClick={() => applyStrategy(key)}>{strategyMode === key ? "Active" : "Apply Strategy"}</button>
              </article>
            ))}
          </div>
        </section>
      )}

      {activeTab === "reports" && (
        <section id="panel-reports" className="panel tab-panel">
          <div className="panel-head-row">
            <div>
              <h2>Reports Vault</h2>
              <p className="muted">Decision memos, score snapshots, and export-ready investment summaries.</p>
            </div>
            <button onClick={saveCurrentReport} disabled={!valuation || !selectedProperty}>
              Save Current Brief
            </button>
          </div>
          <div className="reports-grid">
            {premiumMockFeed.reportTemplates.map((template) => (
              <article key={template.id} className="report-card template-card">
                <h3>{template.name}</h3>
                <small>
                  {template.sections} sections • {template.sla}
                </small>
              </article>
            ))}
            {savedReports.map((report) => (
              <article key={report.id} className="report-card">
                <h3>{report.address}</h3>
                <small>
                  {report.suburb} | score {safeNumber(report.score).toFixed(2)} | confidence {report.confidence}%
                </small>
                <ul className="detail-list">
                  {report.summary.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>
      )}

      {activeTab === "briefs" && (
        <section id="panel-briefs" className="panel tab-panel">
          <h2>Latest Investment Brief</h2>
          {!valuation ? (
            <p className="muted">Run analysis from Trending, Watchlist, or Comparison to generate a brief.</p>
          ) : (
            <>
              <div className="spotlight-banner">
                <strong>Executive summary:</strong> Current brief indicates {valuation.score >= 7 ? "high-conviction" : valuation.score >= 5 ? "balanced" : "watchlist-level"} opportunity quality under the active strategy mandate.
              </div>
              <div className="valuation-headline-row">
                <span className={`score-chip ${scoreTone}`}>Investment Score {valuation.score.toFixed(2)}</span>
                <span className="rank-badge">Confidence {valuation.confidence_pct}%</span>
              </div>
              <div className="valuation-range">
                <NumberPill label="Low Estimate" value={formatMoney(valuation.low_estimate)} />
                <NumberPill label="Mid Estimate" value={formatMoney(valuation.mid_estimate)} />
                <NumberPill label="High Estimate" value={formatMoney(valuation.high_estimate)} />
              </div>
              <section className="panel columns brief-inner-panel">
                <div>
                  <h3>Top Reasons</h3>
                  <ul className="detail-list">
                    {valuation.reasons.slice(0, 6).map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3>Strategy Fit</h3>
                  <div className="fit-chip-wrap">
                    {valuation.deep_analysis.strategy_fit.map((fit) => (
                      <span key={fit} className="fit-chip">
                        {fit}
                      </span>
                    ))}
                  </div>
                </div>
              </section>
              <details className="assumption-disclosure">
                <summary>Show model assumptions</summary>
                <ul className="detail-list">
                  <li>Comparables weighted by structure, recency, and proximity.</li>
                  <li>Risk regime incorporates macro sensitivity and local liquidity.</li>
                  <li>Confidence score penalizes stale freshness and sparse comps.</li>
                </ul>
              </details>
              <div className="artifact-row">
                <button onClick={() => createArtifact("Investment Brief v1")}>Create Investment Brief v1</button>
                <button className="subtle-btn" onClick={() => createArtifact("Negotiation Pack")}>Generate Negotiation Pack</button>
                <button className="subtle-btn" onClick={() => createArtifact("Risk Memo")}>Generate Risk Memo</button>
                <button className="subtle-btn" onClick={() => runResearchPack(valuation.property_id)} disabled={researchLoading}>
                  {researchLoading ? "Running Research..." : "Run Research Engine"}
                </button>
                <button className="subtle-btn" onClick={runPortfolioRiskSimulation} disabled={portfolioRiskLoading}>
                  {portfolioRiskLoading ? "Running Portfolio Risk..." : "Run Portfolio Risk"}
                </button>
              </div>
              {researchPack && (
                <section className="panel brief-inner-panel">
                  <h3>Research Engine</h3>
                  <p className="muted">
                    Underwriting analytics generated from current valuation and market assumptions.
                  </p>
                  <div className="valuation-range">
                    <NumberPill label="DSCR" value={researchPack.underwriting.dscr.toFixed(3)} />
                    <NumberPill label="Monthly Cashflow" value={formatMoney(researchPack.underwriting.monthly_cashflow)} />
                    <NumberPill label="Break-Even Rent" value={`${formatMoney(researchPack.underwriting.break_even_rent_weekly)}/wk`} />
                    <NumberPill label="Cap Rate" value={`${researchPack.underwriting.cap_rate_pct.toFixed(2)}%`} />
                  </div>
                  <div className="context-grid">
                    <div className="context-card">
                      <h3>Acquisition Cost Stack</h3>
                      <p>Stamp duty: {formatMoney(researchPack.acquisition_costs.stamp_duty)}</p>
                      <p>Buyer&apos;s agent: {formatMoney(researchPack.acquisition_costs.buyers_agent_fee)}</p>
                      <p>Total costs: {formatMoney(researchPack.acquisition_costs.total)}</p>
                    </div>
                    <div className="context-card">
                      <h3>Tax Position</h3>
                      <p>After-tax cashflow: {formatMoney(researchPack.tax_position.after_tax_cashflow)}</p>
                      <p>Tax shield: {formatMoney(researchPack.tax_position.tax_shield)}</p>
                      <p>Estimated CGT on exit: {formatMoney(researchPack.tax_position.estimated_cgt_on_exit)}</p>
                    </div>
                  </div>
                  <div className="context-grid">
                    <div className="context-card">
                      <h3>Serviceability</h3>
                      <p>Assessment rate: {researchPack.serviceability.assessment_rate_pct}%</p>
                      <p>Debt service (buffered): {formatMoney(researchPack.serviceability.assessment_debt_service)}</p>
                      <p>Surplus income: {formatMoney(researchPack.serviceability.net_surplus_income)}</p>
                    </div>
                    <div className="context-card">
                      <h3>Optimizer Recommendation</h3>
                      <p>Recommended mode: {researchPack.strategy_optimizer.recommended_mode}</p>
                      <p>Growth score: {researchPack.strategy_optimizer.growth_score}</p>
                      <p>Cashflow score: {researchPack.strategy_optimizer.cashflow_score}</p>
                    </div>
                  </div>
                  <div className="context-grid">
                    <div className="context-card">
                      <h3>5Y Equity Projection</h3>
                      <p>
                        Net equity after costs: {formatMoney(researchPack.equity_projection.net_equity_after_costs)}
                      </p>
                      <p>
                        Projected value: {formatMoney(researchPack.equity_projection.projected_value)}
                      </p>
                    </div>
                    <div className="context-card">
                      <h3>Assumptions</h3>
                      <p>
                        LVR {researchPack.assumptions.lvr_pct}% • Rate {researchPack.assumptions.interest_rate_pct}% • {researchPack.assumptions.loan_years}y loan
                      </p>
                      <p>
                        Expense ratio {researchPack.assumptions.expense_ratio_pct}% • Vacancy {researchPack.assumptions.vacancy_weeks}w
                      </p>
                    </div>
                  </div>
                  <div className="context-grid">
                    <div className="context-card">
                      <h3>Risk Overlays</h3>
                      <p>Liquidity risk: {researchPack.risk_overlays.liquidity_risk_score}</p>
                      <p>Vacancy risk: {researchPack.risk_overlays.vacancy_risk_score}</p>
                      <p>Climate exposure: {researchPack.risk_overlays.climate_exposure_flag}</p>
                    </div>
                    <div className="context-card">
                      <h3>Confidence Breakdown</h3>
                      <p>Comp coverage: {researchPack.confidence_breakdown.comp_coverage}%</p>
                      <p>Market stability: {researchPack.confidence_breakdown.market_stability}%</p>
                      <p>Model confidence: {researchPack.confidence_breakdown.model_confidence}%</p>
                    </div>
                  </div>
                  <div className="deals-table-wrap">
                    <table className="deals-table">
                      <thead>
                        <tr>
                          <th>Interest Rate</th>
                          <th>Annual Debt Service</th>
                          <th>DSCR</th>
                          <th>Annual Cashflow</th>
                        </tr>
                      </thead>
                      <tbody>
                        {researchPack.interest_sensitivity.map((row) => (
                          <tr key={`rate-${row.rate_pct}`}>
                            <td>{row.rate_pct.toFixed(2)}%</td>
                            <td>{formatMoney(row.annual_debt_service)}</td>
                            <td>{row.dscr.toFixed(3)}</td>
                            <td>{formatMoney(row.annual_cashflow)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="deals-table-wrap">
                    <table className="deals-table">
                      <thead>
                        <tr>
                          <th>Scenario</th>
                          <th>Forecast Mid Value</th>
                          <th>Cashflow Delta</th>
                          <th>Risk Shift</th>
                        </tr>
                      </thead>
                      <tbody>
                        {researchPack.scenario_lab.map((row) => (
                          <tr key={row.scenario}>
                            <td>{row.scenario}</td>
                            <td>{formatMoney(row.forecast_mid_value)}</td>
                            <td>{formatMoney(row.expected_cashflow_delta_annual)}</td>
                            <td>{row.risk_shift.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}
              {portfolioRisk && (
                <section className="panel brief-inner-panel">
                  <h3>Portfolio Risk Cockpit</h3>
                  <div className="valuation-range">
                    <NumberPill label="Holdings" value={portfolioRisk.holdings} />
                    <NumberPill label="Aggregate Value" value={formatMoney(portfolioRisk.aggregate_value)} />
                    <NumberPill label="Weighted DSCR" value={portfolioRisk.weighted_dscr.toFixed(3)} />
                    <NumberPill label="Stress Cashflow (+150bps)" value={formatMoney(portfolioRisk.stress_test_rate_up_150bps_cashflow)} />
                  </div>
                  <div className="context-grid">
                    <div className="context-card">
                      <h3>Portfolio Totals</h3>
                      <p>Debt: {formatMoney(portfolioRisk.aggregate_debt)}</p>
                      <p>NOI: {formatMoney(portfolioRisk.aggregate_noi)}</p>
                      <p>Cashflow: {formatMoney(portfolioRisk.aggregate_cashflow)}</p>
                    </div>
                    <div className="context-card">
                      <h3>Concentration Risk</h3>
                      <p>Score: {portfolioRisk.concentration_risk_score.toFixed(2)} / 10</p>
                      <p>Lower is better. Aim for diversified exposure across multiple submarkets.</p>
                    </div>
                  </div>
                </section>
              )}
            </>
          )}
        </section>
      )}

      <section className="panel secondary-summary-panel">
        <h2>Trending Suburbs</h2>
        <ul className="rank-list professional-rank-list">
          {rankings.slice(0, 6).map((r) => (
            <li key={`${r.postcode}-${r.suburb}`}>
              <div>
                <span>
                  {r.suburb}, {r.state}
                </span>
                <small>
                  median {formatMoney(r.median_price)} | growth {r.annual_growth_pct.toFixed(1)}%
                </small>
              </div>
              <strong className="rank-badge">{r.investment_score.toFixed(2)}</strong>
            </li>
          ))}
        </ul>
      </section>

      {artifacts.length > 0 && (
        <section className="panel artifact-log-panel">
          <h2>Recent Artifacts</h2>
          <ul className="artifact-log-list">
            {artifacts.map((item) => (
              <li key={item.id}>
                <strong>{item.title}</strong>
                <small>{item.note}</small>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
