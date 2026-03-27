import React from "react";

import AnalysisApp from "./pages/AnalysisApp";
import LandingPage from "./pages/LandingPage";

export default function App() {
  const path = typeof window !== "undefined" ? window.location.pathname : "/";
  return path.startsWith("/app") ? <AnalysisApp /> : <LandingPage />;
}
