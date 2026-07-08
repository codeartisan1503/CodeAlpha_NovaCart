// Firebase Configuration
// If you want to connect to a live Firebase project, replace the values below.
// If left as-is, NovaCart runs in "Mock Database & Auth Mode" using Django endpoints and localStorage.
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_AUTH_DOMAIN",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_STORAGE_BUCKET",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// Check if we should fallback to local Mock Services
const isFirebaseMock = !firebaseConfig.apiKey || firebaseConfig.apiKey.startsWith("YOUR_");
window.isFirebaseMock = isFirebaseMock;
window.firebaseConfig = firebaseConfig;
