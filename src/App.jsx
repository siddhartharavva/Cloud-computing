import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Bell,
  CheckCircle2,
  Cloud,
  Database,
  FileLock2,
  FileUp,
  Gauge,
  KeyRound,
  Loader2,
  LockKeyhole,
  LogOut,
  MonitorCheck,
  RefreshCcw,
  ShieldCheck,
  ShieldX,
  Timer,
  Trash2,
  UploadCloud,
  UserRound,
  Workflow,
  XCircle
} from "lucide-react";
import { awsConfig, buildCognitoLoginUrl, readTokenFromUrl } from "./config/aws";
import { demoFiles, demoLogs, demoMetrics, demoUser } from "./data/demoData";
import {
  deleteFile,
  getDashboard,
  getLogs,
  getSecureAccess,
  triggerTestAlert,
  uploadFile,
  verifyAccess
} from "./services/api";

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: Gauge },
  { id: "upload", label: "Upload", icon: FileUp },
  { id: "access", label: "Access", icon: ShieldCheck },
  { id: "logs", label: "Monitoring & Alerts", icon: Activity }
];

function App() {
  const [user, setUser] = useState(null);
  const [activeView, setActiveView] = useState("dashboard");
  const [files, setFiles] = useState(awsConfig.demoMode ? demoFiles : []);
  const [metrics, setMetrics] = useState(awsConfig.demoMode ? demoMetrics : {
    totalFiles: 0, verifiedAccess: 0, blockedAttempts: 0, expiringToday: 0
  });
  const [logs, setLogs] = useState(awsConfig.demoMode ? demoLogs : []);
  const [toast, setToast] = useState("");

  useEffect(() => {
    const token = readTokenFromUrl();
    const saved = readSavedUser();
    if (token) {
      let email = "cognito-user@aws";
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        if (payload.email) email = payload.email;
      } catch (e) {}

      const signedIn = { email, token };
      setUser(signedIn);
      saveUser(signedIn);
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (saved) {
      setUser(saved);
    }
  }, []);

  async function refreshDashboard() {
    if (!user) return;
    try {
      const data = await getDashboard(user.token);
      setMetrics(data.metrics || demoMetrics);
      setFiles(data.files || demoFiles);
      setLogs(data.logs || demoLogs);
    } catch (error) {
      setToast(error.message);
    }
  }

  useEffect(() => {
    refreshDashboard();
  }, [user]);

  useEffect(() => {
    const handleExpired = () => {
      logout();
      setTimeout(() => alert("Your session has expired. Please log in again to continue accessing or uploading files."), 100);
    };
    window.addEventListener("session-expired", handleExpired);
    return () => window.removeEventListener("session-expired", handleExpired);
  }, []);

  function handleCognitoLogin() {
    const url = buildCognitoLoginUrl();
    if (!url) {
      setToast("Add Cognito domain and client ID in .env.");
      return;
    }
    window.location.href = url;
  }

  function logout() {
    setUser(null);
    localStorage.removeItem("zt-user");
  }

  function pageTitle(id) {
    return navItems.find(n => n.id === id)?.label || "Dashboard";
  }

  if (!user) {
    return <LoginScreen onCognitoLogin={handleCognitoLogin} />;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <LockKeyhole size={24} />
          </div>
          <div>
            <strong>Zero Trust Exchange</strong>
            <span>AWS Serverless Platform</span>
          </div>
        </div>

        <nav className="nav-list" aria-label="Primary">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={activeView === item.id ? "nav-item active" : "nav-item"}
                onClick={() => setActiveView(item.id)}
                title={item.label}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-status">
          <Cloud size={18} />
          <div>
            <strong>{awsConfig.demoMode ? "Demo Mode" : "AWS Connected"}</strong>
            <span>{awsConfig.region}</span>
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">Cloud Native Secure Data Exchange</span>
            <h1>{pageTitle(activeView)}</h1>
          </div>
          <div className="user-chip">
            <UserRound size={18} />
            <span>{user.email}</span>
            <button className="icon-button" onClick={logout} title="Logout">
              <LogOut size={17} />
            </button>
          </div>
        </header>

        {toast && (
          <div className="toast" role="status">
            <span>{toast}</span>
            <button onClick={() => setToast("")} title="Dismiss">
              <XCircle size={18} />
            </button>
          </div>
        )}

        {activeView === "dashboard" && <Dashboard metrics={metrics} files={files} logs={logs} />}
        {activeView === "upload" && (
          <UploadPanel
            token={user.token}
            onUploaded={(file) => {
              refreshDashboard();
              setToast(file.message || "Upload complete.");
            }}
          />
        )}
        {activeView === "access" && (
          <AccessPanel
            token={user.token}
            files={files}
            onDeleted={(fileId, message) => {
              refreshDashboard();
              setToast(message);
            }}
          />
        )}
        {activeView === "logs" && (
          <LogsPanel
            token={user.token}
            logs={logs}
            setLogs={setLogs}
            onToast={setToast}
          />
        )}
      </main>
    </div>
  );
}

function LoginScreen({ onCognitoLogin }) {
  return (
    <main className="login-screen">
      <section className="login-visual" aria-label="Platform preview">
        <div className="visual-grid">
          <div className="visual-node primary"><ShieldCheck />Cognito</div>
          <div className="visual-node"><Cloud />API Gateway</div>
          <div className="visual-node"><KeyRound />Lambda ZT</div>
          <div className="visual-node"><Database />DynamoDB</div>
          <div className="visual-node"><FileLock2 />S3 + KMS</div>
          <div className="visual-node danger"><Bell />SNS Alert</div>
        </div>
      </section>
      <section className="login-panel">
        <span className="eyebrow">AWS Zero Trust Project</span>
        <h1>Secure, time-bound file exchange with continuous verification.</h1>
        <p>
          Frontend for upload, access verification, monitoring logs, lifecycle expiry,
          and suspicious access alerts.
        </p>
        <div className="login-actions">
          <button className="primary-button" onClick={onCognitoLogin}>
            <UserRound size={18} />
            Cognito Login
          </button>
        </div>
        <div className="login-services">
          S3 · Lambda · API Gateway · Cognito · DynamoDB · EventBridge · CloudWatch · CloudTrail · GuardDuty · SNS · KMS · IAM
        </div>
      </section>
    </main>
  );
}

function Dashboard({ metrics, files, logs }) {
  const cards = [
    { label: "Secure files", value: metrics.totalFiles, icon: FileLock2, tone: "blue" },
    { label: "Verified access", value: metrics.verifiedAccess, icon: CheckCircle2, tone: "green" },
    { label: "Blocked attempts", value: metrics.blockedAttempts, icon: ShieldX, tone: "red" },
    { label: "Expiring today", value: metrics.expiringToday, icon: Timer, tone: "amber" }
  ];

  return (
    <div className="content-grid">
      <section className="metric-grid">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <article className={`metric-card ${card.tone}`} key={card.label}>
              <Icon size={22} />
              <span>{card.label}</span>
              <strong>{card.value}</strong>
            </article>
          );
        })}
      </section>

      <section className="panel wide">
        <div className="panel-header">
          <div>
            <h2>Protected Files</h2>
            <p>S3 objects encrypted with KMS and governed by DynamoDB policy metadata.</p>
          </div>
        </div>
        <FileTable files={files.slice(0, 5)} />
      </section>

      <section className="panel">
        <h2>Verification Health</h2>
        <div className="trust-score">
          <div className="score-ring">96</div>
          <div>
            <strong>Zero Trust score</strong>
            <span>Average policy confidence across recent requests.</span>
          </div>
        </div>
        <div className="health-list">
          <span>Avg Lambda verification: {metrics.avgVerificationMs} ms</span>
          <span>Active access policies: {metrics.activePolicies}</span>
          <span>CloudTrail audit: Recording</span>
        </div>
      </section>

      <section className="panel">
        <h2>Recent Security Events</h2>
        <LogList logs={logs.slice(0, 4)} compact />
      </section>
    </div>
  );
}

function UploadPanel({ token, onUploaded }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [form, setForm] = useState({
    classification: "Confidential",
    expiryHours: "24",
    requireMfa: true,
    allowedIp: "10.0.0.0/24",
    requireTrustedDevice: true,
    allowedRoles: {
      Admins: true,
      Analysts: true,
      Guests: false
    }
  });
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState("");

  useEffect(() => {
    if (form.classification === "Confidential") {
      setForm(prev => ({
        ...prev,
        allowedRoles: { ...prev.allowedRoles, Analysts: false, Guests: false }
      }));
    } else if (form.classification === "Internal") {
      setForm(prev => ({
        ...prev,
        allowedRoles: { ...prev.allowedRoles, Guests: false }
      }));
    }
  }, [form.classification]);

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setProgress(0);
    setUploadResult(null);
    setUploadError("");

    try {
      const uploadForm = {
        classification: form.classification,
        expiryHours: form.expiryHours,
        allowedIp: form.allowedIp || "0.0.0.0/0",
        requireMfa: form.requireMfa,
        allowedRoles: Object.keys(form.allowedRoles).filter(r => form.allowedRoles[r]).join(","),
        policy: [
          form.requireMfa && "MFA",
          form.allowedIp && `IP restricted`,
          form.requireTrustedDevice && "trusted device"
        ].filter(Boolean).join(" + ") || "Open Access"
      };

      const result = await uploadFile({ file: selectedFile, form: uploadForm }, token, setProgress);
      setUploadResult(result);
      onUploaded(result);
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel page-panel">
      <div className="panel-header">
        <div>
          <h2>Secure File Upload</h2>
          <p>Uploads files directly to the FastAPI backend for local zero trust verification workflows.</p>
        </div>
        <UploadCloud size={28} />
      </div>

      <form className="upload-form" onSubmit={handleSubmit}>
        <label className="drop-zone">
          <FileUp size={34} />
          <strong>{selectedFile ? selectedFile.name : "Choose a file for secure upload"}</strong>
          <span>{selectedFile ? `${Math.round(selectedFile.size / 1024)} KB selected` : "PDF, image, ZIP, CSV, or document"}</span>
          <input type="file" onChange={(event) => setSelectedFile(event.target.files?.[0] || null)} />
        </label>

        <div className="form-grid">
          <label>
            Classification
            <select value={form.classification} onChange={(event) => setForm({ ...form, classification: event.target.value })}>
              <option>Internal</option>
              <option>Confidential</option>
              <option>Restricted</option>
            </select>
          </label>
          <label>
            Expiry window
            <select value={form.expiryHours} onChange={(event) => setForm({ ...form, expiryHours: event.target.value })}>
              <option value="0.01666667">1 minute</option>
              <option value="0.16666667">10 minutes</option>
              <option value="1">1 hour</option>
              <option value="6">6 hours</option>
              <option value="24">24 hours</option>
              <option value="72">72 hours</option>
            </select>
          </label>
        </div>

        <div className="policy-checkboxes">
          <strong>Allowed Roles</strong>
          <div style={{ display: "flex", gap: "24px", marginBottom: "8px" }}>
            <label className="toggle-row">
              <input
                type="checkbox"
                checked={form.allowedRoles.Admins}
                onChange={(event) => setForm({ ...form, allowedRoles: { ...form.allowedRoles, Admins: event.target.checked } })}
              />
              <span>Admins</span>
            </label>
            <label className="toggle-row">
              <input
                type="checkbox"
                checked={form.allowedRoles.Analysts}
                disabled={form.classification === "Confidential"}
                onChange={(event) => setForm({ ...form, allowedRoles: { ...form.allowedRoles, Analysts: event.target.checked } })}
              />
              <span>Analysts</span>
            </label>
            <label className="toggle-row">
              <input
                type="checkbox"
                checked={form.allowedRoles.Guests}
                disabled={form.classification === "Confidential" || form.classification === "Internal"}
                onChange={(event) => setForm({ ...form, allowedRoles: { ...form.allowedRoles, Guests: event.target.checked } })}
              />
              <span>Guests</span>
            </label>
          </div>
        </div>

        <div className="policy-checkboxes">
          <strong>Access Policy Requirements</strong>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={form.requireMfa}
              onChange={(event) => setForm({ ...form, requireMfa: event.target.checked })}
            />
            <span>Require MFA verified Cognito identity</span>
          </label>
          <label className="toggle-row" style={{ flexDirection: "column", alignItems: "flex-start", gap: "0.2rem" }}>
            <span>Allowed IP Range (CIDR)</span>
            <input
              type="text"
              value={form.allowedIp}
              onChange={(event) => setForm({ ...form, allowedIp: event.target.value })}
              placeholder="e.g. 10.0.0.0/24 or 0.0.0.0/0"
              style={{ width: "100%", padding: "0.5rem", borderRadius: "4px", border: "1px solid var(--border)", background: "var(--panel-bg)", color: "var(--text-main)" }}
            />
          </label>
          <label className="toggle-row">
            <input
              type="checkbox"
              checked={form.requireTrustedDevice}
              onChange={(event) => setForm({ ...form, requireTrustedDevice: event.target.checked })}
            />
            <span>Require Trusted Device posture</span>
          </label>
        </div>

        <div className="progress-track" aria-label="Upload progress">
          <span style={{ width: `${progress}%` }} />
        </div>

        <button className="primary-button" disabled={busy || !selectedFile}>
          <UploadCloud size={18} />
          {busy ? `Uploading ${progress}%` : "Upload File"}
        </button>

        {uploadResult && (
          <div className="form-message success" role="status">
            <strong>Uploaded {uploadResult.filename || uploadResult.name} successfully.</strong>
            {uploadResult.file_id && <span>File ID: {uploadResult.file_id}</span>}
            {uploadResult.s3_key && <span>S3 key: {uploadResult.s3_key}</span>}
          </div>
        )}

        {uploadError && (
          <div className="form-message error" role="alert">
            {uploadError}
          </div>
        )}
      </form>
    </section>
  );
}

function AccessPanel({ token, files, onDeleted }) {
  const [selectedId, setSelectedId] = useState("");
  const [context, setContext] = useState({
    deviceTrust: "trusted",
    role: "analyst"
  });
  const [decision, setDecision] = useState(null);
  const [signedUrl, setSignedUrl] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (files.length > 0 && !files.find(f => f.id === selectedId)) {
      setSelectedId(files[0].id);
    }
  }, [files, selectedId]);

  const selectedFile = useMemo(
    () => files.find((file) => file.id === selectedId) || files[0],
    [files, selectedId]
  );

  async function runVerification() {
    setIsVerifying(true);
    try {
      const result = await verifyAccess({ fileId: selectedFile?.id, ...context }, token);
      setDecision(result);
      setSignedUrl("");
    } finally {
      setIsVerifying(false);
    }
  }

  async function requestAccess() {
    setIsGenerating(true);
    try {
      const result = await getSecureAccess(selectedFile.id, token);
      setSignedUrl(result.signedUrl);
    } finally {
      setIsGenerating(false);
    }
  }

  async function removeFile() {
    setIsDeleting(true);
    try {
      const result = await deleteFile(selectedFile.id, token);
      onDeleted(selectedFile.id, result.message);
      setDecision(null);
    } catch (error) {
      let msg = error.message;
      try {
        const parsed = JSON.parse(msg);
        if (parsed.detail) msg = parsed.detail;
      } catch(e) {}
      alert(`Deletion Failed: ${msg}`);
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="split-layout">
      <section className="panel">
        <h2>Access Request</h2>
        <div className="form-grid single">
          <label>
            Select file
            <select value={selectedFile?.id || ""} onChange={(event) => setSelectedId(event.target.value)}>
              {files.map((file) => <option key={file.id} value={file.id}>{file.name}</option>)}
            </select>
          </label>

          <label>
            Device trust
            <select value={context.deviceTrust} onChange={(event) => setContext({ ...context, deviceTrust: event.target.value })}>
              <option value="trusted">Trusted device</option>
              <option value="untrusted">Untrusted device</option>
            </select>
          </label>

        </div>


        <div className="button-row">
          <button className="primary-button" onClick={runVerification} disabled={isVerifying}>
            {isVerifying ? <Loader2 size={18} className="spin" /> : <ShieldCheck size={18} />}
            {isVerifying ? "Verifying..." : "Verify Access"}
          </button>
          <button className="secondary-button" onClick={requestAccess} disabled={!decision || decision.decision !== "ALLOW" || isGenerating}>
            {isGenerating ? <Loader2 size={18} className="spin" /> : <KeyRound size={18} />}
            {isGenerating ? "Generating..." : "Generate URL"}
          </button>
          <button className="danger-button" onClick={removeFile} disabled={!selectedFile || isDeleting}>
            {isDeleting ? <Loader2 size={18} className="spin" /> : <Trash2 size={18} />}
            {isDeleting ? "Deleting..." : "Delete"}
          </button>
        </div>
      </section>

      <section className="panel">
        <h2>Policy Decision</h2>
        {decision ? (
          <div className={decision.decision === "ALLOW" ? "decision allow" : "decision deny"}>
            {decision.decision === "ALLOW" ? <CheckCircle2 size={34} /> : <ShieldX size={34} />}
            <strong>{decision.decision}</strong>
            <span>Trust score: {decision.score}/100</span>
            <p>{decision.reason}</p>
            <div className="check-list">
              {decision.checks.map((check) => (
                <span key={check.name} style={{ color: check.passed ? "var(--green)" : "var(--red)" }}>
                  {check.passed ? <CheckCircle2 size={16} color="var(--green)" /> : <XCircle size={16} color="var(--red)" />}
                  {check.passed ? "Passed:" : "Failed:"} {check.name}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <ShieldCheck size={34} />
            Run a verification request to see continuous policy checks.
          </div>
        )}

        {signedUrl && (
          <div className="signed-url">
            <strong>Temporary secure URL</strong>
            <code>{signedUrl}</code>
          </div>
        )}
      </section>
    </div>
  );
}

function LogsPanel({ token, logs, setLogs, onToast }) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  async function refreshLogs() {
    setIsRefreshing(true);
    try {
      const data = await getLogs(token);
      setLogs(data.logs || []);
      onToast("Logs refreshed from CloudWatch-style stream.");
    } finally {
      setIsRefreshing(false);
    }
  }

  async function sendAlert() {
    setIsTesting(true);
    try {
      const result = await triggerTestAlert(token);
      onToast(result.message);
    } finally {
      setIsTesting(false);
    }
  }

  return (
    <section className="panel page-panel">
      <div className="panel-header">
        <div>
          <h2>Monitoring and Audit Logs</h2>
          <p>Display CloudWatch events, CloudTrail audit records, GuardDuty findings, and SNS alert status.</p>
        </div>
        <div className="button-row">
          <button className="secondary-button" onClick={refreshLogs} disabled={isRefreshing}>
            {isRefreshing ? <Loader2 size={18} className="spin" /> : <RefreshCcw size={18} />}
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </button>
          <button className="primary-button" onClick={sendAlert} disabled={isTesting}>
            {isTesting ? <Loader2 size={18} className="spin" /> : <Bell size={18} />}
            {isTesting ? "Testing..." : "Test SNS"}
          </button>
        </div>
      </div>
      <LogList logs={logs} />
    </section>
  );
}

function FileTable({ files }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>File</th>
            <th>Class</th>
            <th>Status</th>
            <th>Expiry</th>
            <th>Policy</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => (
            <tr key={file.id}>
              <td>
                <strong>{file.name}</strong>
                <span>{file.size} · {file.owner}</span>
              </td>
              <td>{file.classification}</td>
              <td><span className="status-pill">{file.status}</span></td>
              <td>{formatDate(file.expiry)}</td>
              <td>{file.policy}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LogList({ logs, compact = false }) {
  return (
    <div className={compact ? "log-list compact" : "log-list"}>
      {logs.map((log) => (
        <article className={`log-item ${log.severity}`} key={log.id}>
          <AlertTriangle size={18} />
          <div>
            <strong>{log.service} · {log.type}</strong>
            <span>{log.message}</span>
          </div>
          <time>{log.time}</time>
        </article>
      ))}
    </div>
  );
}

function pageTitle(activeView) {
  const titles = {
    dashboard: "Security Operations Dashboard",
    upload: "Upload and Policy Assignment",
    access: "Zero Trust Access Verification",
    logs: "Monitoring, Audit, and Alerts"
  };
  return titles[activeView];
}

function normalizeUploadedFile(file) {
  return {
    id: file.id || file.file_id || `file-${Date.now()}`,
    name: file.name || file.filename,
    owner: "current-user@team.aws",
    size: "New upload",
    classification: "Confidential",
    status: file.status || "Active",
    expiry: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString(),
    storage: file.storage || file.s3_key || "uploads/new-upload",
    kmsKey: "alias/zt-file-exchange",
    lastAccess: "Just uploaded",
    policy: "MFA + corporate IP + trusted device"
  };
}

function formatDate(value) {
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function readSavedUser() {
  try {
    const raw = localStorage.getItem("zt-user");
    if (!raw) return null;

    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || !parsed.email) {
      localStorage.removeItem("zt-user");
      return null;
    }

    return parsed;
  } catch {
    localStorage.removeItem("zt-user");
    return null;
  }
}

function saveUser(user) {
  try {
    localStorage.setItem("zt-user", JSON.stringify(user));
  } catch {
    // The app can still run if browser storage is blocked.
  }
}

export default App;
