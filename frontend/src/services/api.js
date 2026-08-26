const API_BASE_URL = 'http://127.0.0.1:8000';

async function handleResponse(response) {
  if (response.status === 204) {
    return null;
  }
  const contentType = response.headers.get('content-type') || '';

  const data = contentType.includes('application/json')
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message = typeof data === 'object' && data !== null && 'detail' in data
      ? data.detail
      : 'Request failed';
    throw new Error(message);
  }

  return data;
}

/**
 * Fetch all feature flags from the backend API.
 * @returns {Promise<Array>} Parsed JSON array of flags.
 */
export async function getFlags(environment) {
  const query = environment ? `?environment=${encodeURIComponent(environment)}` : '';
  const response = await fetch(`${API_BASE_URL}/flags${query}`);
  return handleResponse(response);
}

/**
 * Create a new feature flag by sending a validated payload to the API.
 * @param {Object} flag - Feature flag payload to create.
 * @returns {Promise<Object>} Created feature flag payload.
 */
export async function createFlag(flag) {
  const response = await fetch(`${API_BASE_URL}/flags`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(flag),
  });

  return handleResponse(response);
}

/**
 * Update an existing feature flag using its unique key.
 * @param {string} key - Unique feature flag key.
 * @param {Object} flag - Updated feature flag payload.
 * @returns {Promise<Object>} Updated feature flag payload.
 */
export async function updateFlag(key, flag) {
  const response = await fetch(`${API_BASE_URL}/flags/${key}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(flag),
  });

  return handleResponse(response);
}

export async function deleteFlag(key) {
  const response = await fetch(`${API_BASE_URL}/flags/${key}`, {
    method: 'DELETE',
  });
  return handleResponse(response);
}

/**
 * Fetch a single feature flag by its unique key.
 * @param {string} key - Unique feature flag key.
 * @returns {Promise<Object>} Parsed JSON object for the requested flag.
 */
export async function getFlagByKey(key) {
  const response = await fetch(`${API_BASE_URL}/flags/${key}`);
  return handleResponse(response);
}

export async function getEnvironments() {
  const response = await fetch(`${API_BASE_URL}/environments`);
  return handleResponse(response);
}

export async function getFlagEnvironmentOverrides(key) {
  const response = await fetch(`${API_BASE_URL}/flags/${key}/environments`);
  return handleResponse(response);
}

export async function updateFlagEnvironmentOverride(key, environmentId, override) {
  const response = await fetch(`${API_BASE_URL}/flags/${key}/environments/${environmentId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(override),
  });
  return handleResponse(response);
}

export async function evaluateFlag(payload) {
  const response = await fetch(`${API_BASE_URL}/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

export async function getEvaluationMetrics(flagKey, environment = 'development', days = 7) {
  const response = await fetch(`${API_BASE_URL}/analytics/flags/${encodeURIComponent(flagKey)}/evaluations?environment=${encodeURIComponent(environment)}&days=${days}`);
  return handleResponse(response);
}

export async function getAuditLogs(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value);
    }
  });
  const query = params.toString();
  const response = await fetch(`${API_BASE_URL}/audit-logs${query ? `?${query}` : ''}`);
  return handleResponse(response);
}

export async function getCleanupSuggestions(days = 30) {
  const response = await fetch(`${API_BASE_URL}/cleanup/suggestions?days=${days}`);
  return handleResponse(response);
}

export async function markCleanupReviewed(flagKey) {
  const response = await fetch(`${API_BASE_URL}/cleanup/suggestions/${encodeURIComponent(flagKey)}/review`, { method: 'POST' });
  return handleResponse(response);
}

