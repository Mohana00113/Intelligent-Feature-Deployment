const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function buildUrl(path) {
  const normalizedBase = API_BASE_URL.replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

function getErrorMessage(payload, fallbackMessage) {
  if (typeof payload === 'string' && payload.trim()) {
    return payload;
  }

  if (payload && typeof payload === 'object') {
    if (typeof payload.detail === 'string' && payload.detail.trim()) {
      return payload.detail;
    }

    if (typeof payload.message === 'string' && payload.message.trim()) {
      return payload.message;
    }

    if (typeof payload.error === 'string' && payload.error.trim()) {
      return payload.error;
    }
  }

  return fallbackMessage;
}

async function parseJsonSafely(response) {
  const contentType = response.headers.get('content-type') || '';

  if (response.status === 204) {
    return null;
  }

  if (contentType.includes('application/json')) {
    try {
      return await response.json();
    } catch (error) {
      console.warn('Failed to parse JSON response from API:', error);
      return null;
    }
  }

  try {
    return await response.text();
  } catch (error) {
    console.warn('Failed to read response body from API:', error);
    return null;
  }
}

async function request(endpoint, options = {}) {
  const url = buildUrl(endpoint);

  try {
    const response = await fetch(url, options);
    const payload = await parseJsonSafely(response);

    if (!response.ok) {
      const message = getErrorMessage(payload, `Request failed with status ${response.status}.`);
      console.error(`API request failed for ${url}:`, {
        status: response.status,
        statusText: response.statusText,
        payload,
      });
      throw new Error(message);
    }

    return payload;
  } catch (error) {
    if (error instanceof TypeError) {
      const networkMessage = 'Unable to reach the backend server. Please check that it is running and CORS is enabled.';
      console.error(`Network error while calling ${url}:`, error);
      throw new Error(networkMessage);
    }

    if (error instanceof Error) {
      console.error(`API request error for ${url}:`, error);
      throw error;
    }

    console.error(`Unexpected API error for ${url}:`, error);
    throw new Error('An unexpected error occurred while communicating with the API.');
  }
}

export async function getFlags() {
  return request('/flags');
}

export async function createFlag(flag) {
  return request('/flags', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(flag),
  });
}

export async function updateFlag(key, flag) {
  return request(`/flags/${encodeURIComponent(key)}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(flag),
  });
}

export async function getFlagByKey(key) {
  return request(`/flags/${encodeURIComponent(key)}`);
}

export async function deleteFlag(key) {
  return request(`/flags/${encodeURIComponent(key)}`, { method: 'DELETE' });
}

