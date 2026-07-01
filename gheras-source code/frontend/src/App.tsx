import { RouterProvider } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ChildrenProvider } from "./context/ChildrenContext";
import { router } from "./router";

export default function App() {
  return (
    <AuthProvider>
      <ChildrenProvider>
        <RouterProvider router={router} />
      </ChildrenProvider>
    </AuthProvider>
  );
}
