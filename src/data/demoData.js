const now = Date.now();

export const demoUser = {
  name: "Siddharth",
  email: "member3@zerotrust.aws",
  role: "Secure Exchange Operator",
  token: "demo-cognito-jwt-token"
};

export const demoFiles = [
  {
    id: "file-zt-1001",
    name: "Financial-Audit-Q4.pdf",
    owner: "siddharth@team.aws",
    size: "4.8 MB",
    classification: "Confidential",
    status: "Active",
    expiry: new Date(now + 1000 * 60 * 60 * 20).toISOString(),
    storage: "s3://zero-trust-secure-exchange/confidential/Financial-Audit-Q4.pdf",
    kmsKey: "alias/zt-file-exchange",
    lastAccess: "Verified 4 min ago",
    policy: "MFA + corporate IP + device trust"
  },
  {
    id: "file-zt-1002",
    name: "Client-Contract.zip",
    owner: "legal@team.aws",
    size: "18.2 MB",
    classification: "Restricted",
    status: "Expiring Soon",
    expiry: new Date(now + 1000 * 60 * 45).toISOString(),
    storage: "s3://zero-trust-secure-exchange/restricted/Client-Contract.zip",
    kmsKey: "alias/zt-file-exchange",
    lastAccess: "Verified 21 min ago",
    policy: "Token + location + time window"
  },
  {
    id: "file-zt-1003",
    name: "Public-Demo-Flow.png",
    owner: "frontend@team.aws",
    size: "1.1 MB",
    classification: "Internal",
    status: "Active",
    expiry: new Date(now + 1000 * 60 * 60 * 72).toISOString(),
    storage: "s3://zero-trust-secure-exchange/internal/Public-Demo-Flow.png",
    kmsKey: "alias/zt-file-exchange",
    lastAccess: "Uploaded 1 hour ago",
    policy: "Authenticated users only"
  }
];

export const demoLogs = [
  {
    id: "log-1001",
    time: "Now",
    service: "Lambda",
    type: "Access verified",
    message: "Zero Trust engine approved signed URL request for Financial-Audit-Q4.pdf",
    severity: "success"
  },
  {
    id: "log-1002",
    time: "2 min ago",
    service: "GuardDuty",
    type: "Suspicious attempt",
    message: "Request blocked: token valid, but source IP outside allowed policy range",
    severity: "danger"
  },
  {
    id: "log-1003",
    time: "15 min ago",
    service: "EventBridge",
    type: "Lifecycle check",
    message: "Scheduled expiry scan executed and queued 1 object for deletion",
    severity: "warning"
  },
  {
    id: "log-1004",
    time: "31 min ago",
    service: "CloudTrail",
    type: "Audit event",
    message: "S3 GetObject request recorded with requester identity and policy result",
    severity: "info"
  }
];

export const demoMetrics = {
  totalFiles: 128,
  verifiedAccess: 842,
  blockedAttempts: 19,
  expiringToday: 7,
  avgVerificationMs: 184,
  activePolicies: 14
};

export const awsServices = [
  { name: "Cognito", purpose: "Authentication", state: "Online" },
  { name: "API Gateway", purpose: "Secure endpoints", state: "Online" },
  { name: "Lambda", purpose: "Zero Trust engine", state: "Online" },
  { name: "S3", purpose: "Encrypted storage", state: "Online" },
  { name: "DynamoDB", purpose: "Metadata and policies", state: "Online" },
  { name: "KMS", purpose: "Encryption keys", state: "Online" },
  { name: "EventBridge", purpose: "Expiry automation", state: "Scheduled" },
  { name: "CloudWatch", purpose: "Logs and metrics", state: "Streaming" },
  { name: "CloudTrail", purpose: "Audit trail", state: "Recording" },
  { name: "GuardDuty", purpose: "Threat monitoring", state: "Monitoring" },
  { name: "SNS", purpose: "Security alerts", state: "Armed" },
  { name: "IAM", purpose: "Least privilege", state: "Enforced" }
];
