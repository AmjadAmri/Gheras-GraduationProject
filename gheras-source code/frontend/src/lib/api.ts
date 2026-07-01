const LS_KEY = "qura_token";
const SS_KEY = "qura_token";

export function getToken(): string | null {
  return localStorage.getItem(LS_KEY) || sessionStorage.getItem(SS_KEY);
}

export function setToken(token: string, remember = true) {
  if (remember) {
    localStorage.setItem(LS_KEY, token);
    sessionStorage.removeItem(SS_KEY);
  } else {
    sessionStorage.setItem(SS_KEY, token);
    localStorage.removeItem(LS_KEY);
  }
}

export function clearToken() {
  localStorage.removeItem(LS_KEY);
  sessionStorage.removeItem(SS_KEY);
}

async function requestRaw(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = getToken();

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (
    !(options.body instanceof FormData) &&
    !headers["Content-Type"] &&
    options.body !== undefined
  ) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Token ${token}`;
  }

  const res = await fetch(`/api${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed: ${res.status}`);
  }

  return res;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await requestRaw(path, options);

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

async function requestBlob(
  path: string,
  options: RequestInit = {}
): Promise<Blob> {
  const res = await requestRaw(path, options);

  const contentType = res.headers.get("Content-Type") || "";

  if (contentType.includes("application/json")) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || "File is not ready yet");
  }

  return res.blob();
}

function requestBlobWithProgress(
  path: string,
  onProgress?: (progress: number) => void
): Promise<Blob> {
  const token = getToken();

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.open("GET", `/api${path}`, true);
    xhr.responseType = "blob";

    if (token) {
      xhr.setRequestHeader("Authorization", `Token ${token}`);
    }

    xhr.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = Math.round((event.loaded / event.total) * 100);
        onProgress(progress);
      }
    };

    xhr.onload = () => {
      const contentType = xhr.getResponseHeader("Content-Type") || "";

      if (xhr.status >= 200 && xhr.status < 300) {
        if (contentType.includes("application/json")) {
          const reader = new FileReader();

          reader.onload = () => {
            try {
              const body = JSON.parse(String(reader.result || "{}"));
              reject(new Error(body.error || "File is not ready yet"));
            } catch {
              reject(new Error("File is not ready yet"));
            }
          };

          reader.onerror = () => reject(new Error("File is not ready yet"));
          reader.readAsText(xhr.response);
          return;
        }

        resolve(xhr.response);
        return;
      }

      const reader = new FileReader();

      reader.onload = () => {
        try {
          const body = JSON.parse(String(reader.result || "{}"));
          reject(new Error(body.error || `Request failed: ${xhr.status}`));
        } catch {
          reject(new Error(`Request failed: ${xhr.status}`));
        }
      };

      reader.onerror = () => reject(new Error(`Request failed: ${xhr.status}`));
      reader.readAsText(xhr.response);
    };

    xhr.onerror = () => reject(new Error("Network error"));
    xhr.send();
  });
}

export const api = {
  get: <T>(path: string) => request<T>(path),

  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  put: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: <T>(path: string) =>
    request<T>(path, {
      method: "DELETE",
    }),

  postForm: <T>(path: string, data: FormData) =>
    request<T>(path, {
      method: "POST",
      body: data,
    }),

  putForm: <T>(path: string, data: FormData) =>
    request<T>(path, {
      method: "PUT",
      body: data,
    }),

  getBlob: (path: string) => requestBlob(path),

  getBlobWithProgress: (
    path: string,
    onProgress?: (progress: number) => void
  ) => requestBlobWithProgress(path, onProgress),

  download: (path: string) => requestBlob(path),
};