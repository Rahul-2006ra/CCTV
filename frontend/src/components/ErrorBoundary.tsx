import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught runtime error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: "32px", maxWidth: "600px", margin: "40px auto", background: "#1a2024", borderRadius: "8px", border: "1px solid #e07a68", color: "#f0f6fc" }}>
          <h2 style={{ color: "#e07a68", marginBottom: "12px" }}>Something went wrong</h2>
          <p style={{ color: "#8c98a0", fontSize: "14px", marginBottom: "16px" }}>
            An unexpected error occurred in this view.
          </p>
          <pre style={{ background: "#0e1215", padding: "12px", borderRadius: "4px", fontSize: "12px", overflowX: "auto", color: "#ff7b72" }}>
            {this.state.error?.message}
          </pre>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            style={{ marginTop: "16px", padding: "8px 16px", background: "var(--accent, #52c41a)", color: "#000", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: 600 }}
          >
            Reload Application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
