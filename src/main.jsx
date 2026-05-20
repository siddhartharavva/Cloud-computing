import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./styles.css";

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error("App crashed:", error);
  }

  resetApp = () => {
    localStorage.removeItem("zt-user");
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <main className="fatal-screen">
          <section>
            <h1>Frontend could not start</h1>
            <p>
              A saved browser value or runtime setting caused the app to stop.
              Reset the local demo session and open it again.
            </p>
            <button className="primary-button" onClick={this.resetApp}>
              Reset Demo Session
            </button>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </React.StrictMode>
);
