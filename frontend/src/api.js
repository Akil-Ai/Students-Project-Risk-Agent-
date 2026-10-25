const rawBase = import.meta.env.VITE_API_BASE_URL || '';
export const API_BASE = rawBase
  ? (rawBase.endsWith('/api/v1') ? rawBase : `${rawBase.replace(/\/+$/, '')}/api/v1`)
  : '/api/v1';

export const api = {
  getBaseUrl: () => API_BASE,
  getToken: () => localStorage.getItem('token'),
  getUser: () => {
    try {
      const u = localStorage.getItem('user');
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  },
  setAuth: (token, user) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },
  clearAuth: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const headers = {
      ...(options.headers || {}),
    };

    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      this.clearAuth();
      window.location.reload();
      throw new Error('Session expired or unauthorized');
    }

    if (!res.ok) {
      let errMsg = `Request failed (${res.status})`;
      try {
        const errJson = await res.json();
        errMsg = errJson.detail || errMsg;
      } catch {
        // ignore
      }
      throw new Error(errMsg);
    }

    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await res.json();
    }
    return res;
  },

  // Auth
  async login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const res = await fetch(`${API_BASE}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Invalid institutional email or password');
    }
    const data = await res.json();
    this.setAuth(data.access_token, {
      id: data.user_id,
      name: data.name,
      email: data.email,
      role: data.role,
    });
    return data;
  },

  async getMe() {
    return this.request('/auth/me');
  },

  // Overview
  async getOverview() {
    return this.request('/overview');
  },

  // Projects
  async getProjects() {
    return this.request('/projects');
  },

  async getProjectDetails(id) {
    return this.request(`/projects/${id}`);
  },

  async createProject(payload) {
    return this.request('/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async recalculateRisk(projectId) {
    return this.request(`/projects/${projectId}/score`, {
      method: 'POST',
    });
  },

  // Reviews
  async addReview(projectId, payload) {
    return this.request(`/projects/${projectId}/reviews`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateActionItem(itemId, status) {
    return this.request(`/action-items/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  },

  // Progress
  async addProgressLog(projectId, payload) {
    return this.request(`/projects/${projectId}/progress`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Alerts
  async getAlerts() {
    return this.request('/alerts');
  },

  async sendAlertFeedback(alertId, feedback, status) {
    return this.request(`/alerts/${alertId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ feedback, status }),
    });
  },

  // Models
  async getModels() {
    return this.request('/models');
  },

  async retrainModel() {
    return this.request('/models/retrain', {
      method: 'POST',
    });
  },

  // Import
  async uploadBulkFile(entityType, file) {
    const formData = new FormData();
    formData.append('file', file);
    return this.request(`/import/${entityType}`, {
      method: 'POST',
      body: formData,
    });
  },

  // Admin
  async getUsers() {
    return this.request('/admin/users');
  },

  async createUser(payload) {
    return this.request('/admin/users', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getSettings() {
    return this.request('/settings');
  },

  async updateSetting(key, value) {
    return this.request('/settings', {
      method: 'PUT',
      body: JSON.stringify({ key, value }),
    });
  },

  async getScheduler() {
    return this.request('/admin/scheduler');
  },

  // Reports
  async getReportsSummary() {
    return this.request('/reports/summary');
  },
};
