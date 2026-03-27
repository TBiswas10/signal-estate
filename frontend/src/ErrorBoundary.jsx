import React, { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || "Unknown render error" };
  }

  componentDidCatch(error) {
    // Keep this visible in browser console for fast debugging.
    console.error("Frontend render error:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "24px", color: "#102032", fontFamily: "Space Grotesk, sans-serif" }}>
          <h2>Frontend runtime error</h2>
          <p>{this.state.message}</p>
          <p>Hard refresh (Ctrl+F5) and try again.</p>
        </div>
      );
    }

    return this.props.children;
  }
}
