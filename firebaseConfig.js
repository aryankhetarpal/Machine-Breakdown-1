// firebaseConfig.js
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyBcv4fzpYLD7TlqDpyETNc4DWvILy9IXEg",
  authDomain: "machine-break.firebaseapp.com",
  projectId: "machine-break",
  storageBucket: "machine-break.appspot.com",  // corrected bucket URL
  messagingSenderId: "282038884558",
  appId: "1:282038884558:web:b35f4b7e7b7f5c32f1989f",
  measurementId: "G-FRY5ER36P7"
};

const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
