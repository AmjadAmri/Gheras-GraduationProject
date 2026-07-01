import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
import type { Child } from "../types/child";
import { api } from "../lib/api";

interface ChildrenContextValue {
  children: Child[];
  loading: boolean;
  addChild: (data: FormData) => Promise<void>;
  updateChild: (id: number, data: FormData) => Promise<void>;
  deleteChild: (id: number) => Promise<void>;
  getChild: (id: number) => Child | undefined;
  refreshChildren: () => Promise<void>;
}

const ChildrenContext = createContext<ChildrenContextValue | null>(null);

export function ChildrenProvider({ children: reactChildren }: { children: ReactNode }) {
  const [childrenList, setChildrenList] = useState<Child[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchChildren = useCallback(async () => {
    try {
      const data = await api.get<Child[]>("/children/");
      setChildrenList(data);
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChildren();
  }, [fetchChildren]);

  const addChild = useCallback(async (data: FormData) => {
    await api.postForm<Child>("/children/", data);
    await fetchChildren();
  }, [fetchChildren]);

  const updateChild = useCallback(async (id: number, data: FormData) => {
    await api.putForm<Child>(`/children/${id}/`, data);
    await fetchChildren();
  }, [fetchChildren]);

  const deleteChild = useCallback(async (id: number) => {
    await api.delete(`/children/${id}/`);
    await fetchChildren();
  }, [fetchChildren]);

  const getChild = useCallback(
    (id: number) => childrenList.find((c) => c.id === id),
    [childrenList]
  );

  return (
    <ChildrenContext.Provider
      value={{ children: childrenList, loading, addChild, updateChild, deleteChild, getChild, refreshChildren: fetchChildren }}
    >
      {reactChildren}
    </ChildrenContext.Provider>
  );
}

export function useChildren() {
  const context = useContext(ChildrenContext);
  if (!context) throw new Error("useChildren must be used within ChildrenProvider");
  return context;
}
