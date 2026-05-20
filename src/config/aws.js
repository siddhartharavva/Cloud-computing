export const awsConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "",
  region: import.meta.env.VITE_AWS_REGION || "ap-south-1",
  cognitoDomain: import.meta.env.VITE_COGNITO_DOMAIN || "",
  cognitoClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || "",
  cognitoRedirectUri: import.meta.env.VITE_COGNITO_REDIRECT_URI || window.location.origin,
  demoMode: import.meta.env.VITE_DEMO_MODE !== "false"
};

export function buildCognitoLoginUrl() {
  if (!awsConfig.cognitoDomain || !awsConfig.cognitoClientId) return "";

  const params = new URLSearchParams({
    client_id: awsConfig.cognitoClientId,
    response_type: "token",
    scope: "openid email profile",
    redirect_uri: awsConfig.cognitoRedirectUri
  });

  return `${awsConfig.cognitoDomain}/login?${params.toString()}`;
}

export function readTokenFromUrl() {
  const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  return hash.get("id_token") || hash.get("access_token");
}
