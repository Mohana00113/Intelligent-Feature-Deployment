const API_BASE_URL = 'http://localhost:8000';

async function handleResponse(response) {
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
export async function getFlags() {
  const response = await fetch(`${API_BASE_URL}/flags`);
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

/**
 * Fetch a single feature flag by its unique key.
 * @param {string} key - Unique feature flag key.
 * @returns {Promise<Object>} Parsed JSON object for the requested flag.
 */
export async function getFlagByKey(key) {
  const response = await fetch(`${API_BASE_URL}/flags/${key}`);
  return handleResponse(response);
}

/**
 * Delete an existing feature flag by its unique key.
 * @param {string} key - Unique feature flag key.
 * @returns {Promise<void>} Resolves when the delete request succeeds.
 */
export async function deleteFlag(key) {
  const response = await fetch(`${API_BASE_URL}/flags/${encodeURIComponent(key)}`, {
    method: 'DELETE',
  });

  return handleResponse(response);
}

