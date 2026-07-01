import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
import type { User } from "../types/user";
import { api, setToken, clearToken, getToken } from "../lib/api";

interface AuthResponse {
  token: string;
  user: User;
}

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: (email: string, password: string, remember?: boolean) => Promise<void>;
  signUp: (name: string, email: string, password: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const LOGIN_POPUP_KEY = "gheras_show_login_popup";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(!!getToken());

  useEffect(() => {
    const token = getToken();
    if (token) {
      api.get<User>("/auth/me/")
        .then(setUser)
        .catch(() => clearToken())
        .finally(() => setIsLoading(false));
    }
  }, []);

  const signIn = useCallback(async (email: string, password: string, remember = true) => {
    const data = await api.post<AuthResponse>("/auth/signin/", { email, password });
    setToken(data.token, remember);
    setUser(data.user);
  }, []);

  const signUp = useCallback(async (name: string, email: string, password: string) => {
    const data = await api.post<AuthResponse>("/auth/signup/", { name, email, password });
    setToken(data.token);
    setUser(data.user);
    sessionStorage.setItem(LOGIN_POPUP_KEY, "true");
  }, []);

  const signOut = useCallback(() => {
    api.post("/auth/signout/").catch(() => {});
    clearToken();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, isLoading, signIn, signUp, signOut }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
