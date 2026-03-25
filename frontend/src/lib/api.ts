const API_BASE = "";

function formatApiErrorDetail(detail: unknown, status: number): string {
  if (detail == null) return `API Error: ${status}`;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          const loc = "loc" in item && Array.isArray((item as { loc?: unknown }).loc)
            ? `${(item as { loc: unknown[] }).loc.join(".")}: `
            : "";
          return `${loc}${(item as { msg: string }).msg}`;
        }
        try {
          return JSON.stringify(item);
        } catch {
          return String(item);
        }
      })
      .filter(Boolean)
      .join("; ");
  }
  if (typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return String(detail);
    }
  }
  return String(detail);
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(formatApiErrorDetail((error as { detail?: unknown }).detail, res.status));
  }
  return res.json();
}

// Roles
export const api = {
  // Roles
  listRoles: () => request<any[]>("/api/roles"),
  getRole: (id: string) => request<any>(`/api/roles/${id}`),
  createRole: (data: { title: string; jd_text: string; blind_mode?: boolean }) =>
    request<any>("/api/roles", { method: "POST", body: JSON.stringify(data) }),
  analyzeJDPreview: (jdText: string) =>
    request<any>("/api/roles/analyze-jd-preview", {
      method: "POST",
      body: JSON.stringify({ jd_text: jdText }),
    }),
  updateRole: (id: string, data: any) =>
    request<any>(`/api/roles/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteRole: (id: string) =>
    request<any>(`/api/roles/${id}`, { method: "DELETE" }),
  analyzeJD: (id: string) =>
    request<any>(`/api/roles/${id}/analyze-jd`, { method: "POST" }),
  getConfig: (id: string) => request<any>(`/api/roles/${id}/config`),
  updateConfig: (id: string, data: any) =>
    request<any>(`/api/roles/${id}/config`, { method: "PUT", body: JSON.stringify(data) }),

  // Resumes
  listResumes: (roleId: string) => request<any[]>(`/api/roles/${roleId}/resumes`),
  getResume: (id: string) => request<any>(`/api/resumes/${id}`),
  uploadResume: async (roleId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/api/roles/${roleId}/resumes`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiErrorDetail(error.detail, res.status));
    }
    return res.json();
  },
  deleteResume: (id: string) =>
    request<any>(`/api/resumes/${id}`, { method: "DELETE" }),
  searchResumes: (roleId: string, q: string) =>
    request<any[]>(`/api/roles/${roleId}/search?q=${encodeURIComponent(q)}`),
  findSimilar: (resumeId: string) =>
    request<any[]>(`/api/resumes/${resumeId}/similar`),
  batchReparse: (roleId: string) =>
    request<any>(`/api/roles/${roleId}/batch-reparse`, { method: "POST" }),
  multiRoleScore: (resumeId: string, roleIds: string[]) =>
    request<any>(`/api/resumes/${resumeId}/multi-role`, {
      method: "POST",
      body: JSON.stringify({ role_ids: roleIds }),
    }),
};

export function fetcher<T>(path: string): Promise<T> {
  return request<T>(path);
}
