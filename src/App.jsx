import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Bell,
  CheckCircle2,
  Cloud,
  Database,
  FileLock2,
  FileUp,
  Gauge,
  KeyRound,
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
import { awsServices, demoFiles, demoLogs, demoMetrics, demoUser } from "./data/demoData";
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
  { id: "logs", label: "Logs", icon: MonitorCheck },
  { id: "architecture", label: "AWS Flow", icon: Workflow }
];

function App() {
  const [user, setUser] = useState(null);
  const [activeView, setActiveView] = useState("dashboard");
  const [files, setFiles] = useState(demoFiles);
  const [logs, setLogs] = useState(demoLogs);
  const [metrics, setMetrics] = useState(demoMetrics);
  const [toast, setToast] = useState("");

  useEffect(() => {
    const token = readTokenFromUrl();
    const saved = localStorage.getItem("zt-user");
    if (token) {
      const signedIn = { ...demoUser, token };
      setUser(signedIn);
      localStorage.setItem("zt-user", JSON.stringify(signedIn));
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (saved) {
      setUser(JSON.parse(saved));
    }
  }, []);

  useEffect(() => {
    if (!user) return;
    getDashboard(user.token)
      .then((data) => {
        setMetrics(data.metrics || demoMetrics);
        setFiles(data.files || demoFiles);
        setLogs(data.logs || demoLogs);
      })
      .catch((error) => setToast(error.message));
  }, [user]);

  function handleDemoLogin() {
    setUser(demoUser);
    localStorage.setItem("zt-user", JSON.stringify(demoUser));
  }

  function handleCognitoLogin() {
    const url = buildCognitoLoginUrl();
    if (!url) {
      setToast("Add Cognito domain and client ID in .env, or use demo login.");
      return;
    }
    window.location.href = url;
  }

  function logout() {
    setUser(null);
    localStorage.removeItem("zt-user");
  }

  if (!user) {
    return <LoginScreen onDemoLogin={handleDemoLogin} onCognitoLogin={handleCognitoLogin} />;
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
              setFiles((current) => [normalizeUploadedFile(file), ...current]);
              setToast(file.message || "Upload complete.");
            }}
          />
        )}
        {activeView === "access" && (
          <AccessPanel
            token={user.token}
            files={files}
            onDeleted={(fileId, message) => {
              setFiles((current) => current.filter((file) => file.id !== fileId));
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
        {activeView === "architecture" && <ArchitecturePanel />}
      </main>
    </div>
  );
}

function LoginScreen({ onDemoLogin, onCognitoLogin }) {
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
          <button className="primary-button" onClick={onDemoLogin}>
            <ShieldCheck size={18} />
            Demo Login
          </button>
          <button className="secondary-button" onClick={onCognitoLogin}>
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
    allowedIp: "10.0.0.0/24",
    requireMfa: true,
    policy: "MFA + corporate IP + trusted device"
  });
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setProgress(0);
    try {
      const result = await uploadFile({ file: selectedFile, form }, token, setProgress);
      onUploaded(result);
    } catch (error) {
      onUploaded({ message: error.message, name: "Upload failed", status: "Failed" });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel page-panel">
      <div className="panel-header">
        <div>
          <h2>Secure File Upload</h2>
          <p>Uploads request a Lambda pre-signed URL, store encrypted objects in S3, and save policy metadata in DynamoDB.</p>
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
              <option value="1">1 hour</option>
              <option value="6">6 hours</option>
              <option value="24">24 hours</option>
              <option value="72">72 hours</option>
            </select>
          </label>
          <label>
            Allowed IP range
            <input value={form.allowedIp} onChange={(event) => setForm({ ...form, allowedIp: event.target.value })} />
          </label>
          <label>
            Policy rule
            <input value={form.policy} onChange={(event) => setForm({ ...form, policy: event.target.value })} />
          </label>
        </div>

        <label className="toggle-row">
          <input
            type="checkbox"
            checked={form.requireMfa}
            onChange={(event) => setForm({ ...form, requireMfa: event.target.checked })}
          />
          <span>Require MFA verified Cognito identity before file access</span>
        </label>

        <div className="progress-track" aria-label="Upload progress">
          <span style={{ width: `${progress}%` }} />
        </div>

        <button className="primary-button" disabled={busy || !selectedFile}>
          <UploadCloud size={18} />
          {busy ? `Uploading ${progress}%` : "Encrypt and Upload"}
        </button>
      </form>
    </section>
  );
}

function AccessPanel({ token, files, onDeleted }) {
  const [selectedId, setSelectedId] = useState(files[0]?.id || "");
  const [context, setContext] = useState({
    sourceIp: "10.0.0.42",
    deviceTrust: "trusted",
    role: "analyst",
    expired: false
  });
  const [decision, setDecision] = useState(null);
  const [signedUrl, setSignedUrl] = useState("");

  const selectedFile = useMemo(
    () => files.find((file) => file.id === selectedId) || files[0],
    [files, selectedId]
  );

  async function runVerification() {
    const result = await verifyAccess({ fileId: selectedFile?.id, ...context }, token);
    setDecision(result);
    setSignedUrl("");
  }

  async function requestAccess() {
    const result = await getSecureAccess(selectedFile.id, token);
    setSignedUrl(result.signedUrl);
  }

  async function removeFile() {
    const result = await deleteFile(selectedFile.id, token);
    onDeleted(selectedFile.id, result.message);
    setDecision(null);
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
            Source IP
            <input value={context.sourceIp} onChange={(event) => setContext({ ...context, sourceIp: event.target.value })} />
          </label>
          <label>
            Device trust
            <select value={context.deviceTrust} onChange={(event) => setContext({ ...context, deviceTrust: event.target.value })}>
              <option value="trusted">Trusted device</option>
              <option value="untrusted">Untrusted device</option>
            </select>
          </label>
          <label>
            User role
            <select value={context.role} onChange={(event) => setContext({ ...context, role: event.target.value })}>
              <option value="analyst">Analyst</option>
              <option value="admin">Admin</option>
              <option value="guest">Guest</option>
            </select>
          </label>
        </div>

        <label className="toggle-row">
          <input
            type="checkbox"
            checked={context.expired}
            onChange={(event) => setContext({ ...context, expired: event.target.checked })}
          />
          <span>Simulate expired access window</span>
        </label>

        <div className="button-row">
          <button className="primary-button" onClick={runVerification}>
            <ShieldCheck size={18} />
            Verify Access
          </button>
          <button className="secondary-button" onClick={requestAccess} disabled={!decision || decision.decision !== "ALLOW"}>
            <KeyRound size={18} />
            Generate URL
          </button>
          <button className="danger-button" onClick={removeFile} disabled={!selectedFile}>
            <Trash2 size={18} />
            Delete
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
                <span key={check.name}>
                  {check.passed ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                  {check.name}
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
  async function refreshLogs() {
    const data = await getLogs(token);
    setLogs(data.logs || []);
    onToast("Logs refreshed from CloudWatch-style stream.");
  }

  async function sendAlert() {
    const result = await triggerTestAlert(token);
    onToast(result.message);
  }

  return (
    <section className="panel page-panel">
      <div className="panel-header">
        <div>
          <h2>Monitoring and Audit Logs</h2>
          <p>Display CloudWatch events, CloudTrail audit records, GuardDuty findings, and SNS alert status.</p>
        </div>
        <div className="button-row">
          <button className="secondary-button" onClick={refreshLogs}>
            <RefreshCcw size={18} />
            Refresh
          </button>
          <button className="primary-button" onClick={sendAlert}>
            <Bell size={18} />
            Test SNS
          </button>
        </div>
      </div>
      <LogList logs={logs} />
    </section>
  );
}

function ArchitecturePanel() {
  return (
    <div className="content-grid">
      <section className="panel wide">
        <h2>AWS Workflow</h2>
        <div className="flow-diagram">
          {["Cognito Login", "React UI", "API Gateway", "Lambda Zero Trust", "S3 + KMS", "DynamoDB", "CloudWatch", "EventBridge", "SNS Alert"].map((step, index) => (
            <div className="flow-step" key={step}>
              <span>{index + 1}</span>
              <strong>{step}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="panel wide">
        <h2>AWS Services Covered</h2>
        <div className="service-grid">
          {awsServices.map((service) => (
            <article key={service.name} className="service-card">
              <strong>{service.name}</strong>
              <span>{service.purpose}</span>
              <em>{service.state}</em>
            </article>
          ))}
        </div>
      </section>
    </div>
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
    logs: "Monitoring, Audit, and Alerts",
    architecture: "AWS Architecture and Service Coverage"
  };
  return titles[activeView];
}

function normalizeUploadedFile(file) {
  return {
    id: file.id || `file-${Date.now()}`,
    name: file.name,
    owner: "current-user@team.aws",
    size: "New upload",
    classification: "Confidential",
    status: file.status || "Active",
    expiry: new Date(Date.now() + 1000 * 60 * 60 * 24).toISOString(),
    storage: file.storage || "s3://zero-trust-secure-exchange/new-upload",
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

export default App;
