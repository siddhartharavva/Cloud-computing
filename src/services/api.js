import { awsConfig } from "../config/aws";
import { demoFiles, demoLogs, demoMetrics } from "../data/demoData";

const backendBaseUrl = (awsConfig.apiBaseUrl || "http://localhost:8000").replace(/\/$/, "");
const wait = (ms = 500) => new Promise((resolve) => setTimeout(resolve, ms));

async function request(path, options = {}, token = "") {
  if (awsConfig.demoMode || !awsConfig.apiBaseUrl) {
    return mockRequest(path, options);
  }

  const response = await fetch(`${awsConfig.apiBaseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    }
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function getDashboard(token) {
  return request("/dashboard", {}, token);
}

export async function getLogs(token) {
  return request("/logs", {}, token);
}

export async function uploadFile({ file, form }, token, onProgress) {
  if (!file) {
    throw new Error("Choose a file before uploading.");
  }

  const formData = new FormData();
  formData.append("file", file);

  Object.entries(form || {}).forEach(([key, value]) => {
    formData.append(key, String(value));
  });

  onProgress?.(35);

  const response = await fetch(`${backendBaseUrl}/upload`, {
    method: "POST",
    body: formData,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  });

  if (!response.ok) {
    const errorMessage = await readErrorMessage(response);
    throw new Error(errorMessage || `Upload failed with status ${response.status}`);
  }

  onProgress?.(100);

  const result = await response.json();
  return {
    ...result,
    id: result.file_id,
    name: result.filename,
    status: "Active",
    storage: result.s3_key,
    message: result.message || "File uploaded successfully."
  };
}

async function readErrorMessage(response) {
  const contentType = response.headers.get("content-type") || "";

  if (response.status === 413) {
    return "Upload failed because the selected file is too large for the current server limit.";
  }

  if (contentType.includes("application/json")) {
    const body = await response.json();
    return body.error || body.detail || JSON.stringify(body);
  }

  const text = await response.text();
  if (text.trim().startsWith("<")) {
    return `Upload failed with status ${response.status}.`;
  }

  return text;
}

export async function verifyAccess(payload, token) {
  return request("/verify", {
    method: "POST",
    body: JSON.stringify(payload)
  }, token);
}

export async function getSecureAccess(fileId, token) {
  return request(`/access?fileId=${encodeURIComponent(fileId)}`, {}, token);
}

export async function deleteFile(fileId, token) {
  return request(`/delete/${encodeURIComponent(fileId)}`, { method: "DELETE" }, token);
}

export async function triggerTestAlert(token) {
  return request("/alerts/test", { method: "POST", body: JSON.stringify({ type: "demo-suspicious-access" }) }, token);
}

async function mockRequest(path, options = {}) {
  await wait();

  if (path === "/dashboard") {
    return { metrics: demoMetrics, files: demoFiles, logs: demoLogs };
  }

  if (path === "/logs") return { logs: demoLogs };

  if (path === "/upload") {
    const body = JSON.parse(options.body || "{}");
    return {
      id: `file-zt-${Math.floor(Math.random() * 9000) + 1000}`,
      name: body.name || body.fileName || "Uploaded-File.dat",
      status: "Active",
      storage: `s3://zero-trust-secure-exchange/${body.classification || "internal"}/${body.name || "Uploaded-File.dat"}`,
      message: "File encrypted, uploaded to S3, and metadata saved in DynamoDB."
    };
  }

  if (path === "/verify") {
    const body = JSON.parse(options.body || "{}");
    const denied = body.sourceIp?.startsWith("203.") || body.deviceTrust === "untrusted" || body.expired === true;
    return {
      decision: denied ? "DENY" : "ALLOW",
      score: denied ? 42 : 96,
      reason: denied
        ? "Access denied because request context violates IP/device policy."
        : "Access approved. Token, expiry, IP, role, and device trust checks passed.",
      checks: [
        { name: "Cognito token", passed: true },
        { name: "Expiry window", passed: !body.expired },
        { name: "IP policy", passed: !body.sourceIp?.startsWith("203.") },
        { name: "Device trust", passed: body.deviceTrust !== "untrusted" },
        { name: "DynamoDB policy", passed: true }
      ]
    };
  }

  if (path.startsWith("/access")) {
    return {
      signedUrl: "https://s3.ap-south-1.amazonaws.com/demo-presigned-url",
      expiresIn: "5 minutes",
      message: "Temporary pre-signed URL generated."
    };
  }

  if (path.startsWith("/delete")) {
    return { message: "File deleted from S3 and metadata marked expired." };
  }

  if (path === "/alerts/test") {
    return { message: "SNS alert sent to the security notification topic." };
  }

  return {};
}
