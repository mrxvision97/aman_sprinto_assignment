const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API Error: ${res.status}`);
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
      throw new Error(error.detail || `Upload Error: ${res.status}`);
    }
    return res.json();
  },
  deleteResume: (id: string) =>
    request<any>(`/api/resumes/${id}`, { method: "DELETE" }),
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
