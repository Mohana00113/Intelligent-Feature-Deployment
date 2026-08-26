import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import FeatureFlagForm from '../components/FeatureFlagForm';
import { createFlag, deleteFlag, getFlags, updateFlag } from '../services/api';
import { useEnvironment } from '../context/EnvironmentContext';

const createInitialForm = () => ({
  key: '',
  type: 'boolean',
  default_value: true,
  enabled: true,
  rollout_percentage: 0,
  description: '',
  owner_team: '',
  environment_id: 1,
  target_users: [],
});

function FeatureFlags({ flags: controlledFlags, loading: controlledLoading, error: controlledError, onRefresh }) {
  const navigate = useNavigate();
  const { environment } = useEnvironment();
  const isControlled = typeof controlledFlags !== 'undefined';

  const [internalFlags, setInternalFlags] = useState([]);
  const [loading, setLoading] = useState(!isControlled);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState(createInitialForm);
  const [formErrors, setFormErrors] = useState({});
  const [formMode, setFormMode] = useState('create');
  const [editingFlag, setEditingFlag] = useState(null);

  const environmentId = { development: 1, staging: 2, production: 3 }[environment];
  const allFlags = isControlled ? (Array.isArray(controlledFlags) ? controlledFlags : []) : internalFlags;
  const flags = allFlags.filter((flag) => flag.environment_id === environmentId);
  const currentLoading = isControlled ? Boolean(controlledLoading) : loading;
  const currentError = isControlled ? controlledError : error;

  const environmentOptions = useMemo(() => [
    { value: 1, label: 'Development' },
    { value: 2, label: 'Staging' },
    { value: 3, label: 'Production' },
  ], []);

  const loadFlags = useCallback(async () => {
    if (isControlled) {
      if (onRefresh) {
        await onRefresh();
      }
      return;
    }

    try {
      setLoading(true);
      setError('');
      const data = await getFlags();
      setInternalFlags(Array.isArray(data) ? data : []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load feature flags.';
      console.error('Failed to fetch feature flags:', err);
      setError(message);
      setInternalFlags([]);
    } finally {
      setLoading(false);
    }
  }, [isControlled, onRefresh]);

  useEffect(() => {
    if (isControlled) {
      return undefined;
    }

    let isMounted = true;

    async function fetchFlags() {
      try {
        if (!isMounted) {
          return;
        }
        await loadFlags();
      } catch (err) {
        console.error('Feature flag list refresh failed:', err);
      }
    }

    void fetchFlags();

    return () => {
      isMounted = false;
    };
  }, [isControlled, loadFlags]);

  const handleOpenModal = (flag = null) => {
    if (flag) {
      setForm({
        key: flag.key,
        type: flag.type || 'boolean',
        default_value: Boolean(flag.default_value),
        enabled: flag.enabled ?? true,
        rollout_percentage: Number(flag.rollout_percentage ?? 0),
        description: flag.description || '',
        owner_team: flag.owner_team || '',
        environment_id: flag.environment_id || 1,
        target_users: flag.target_users || [],
      });
      setFormMode('edit');
      setEditingFlag(flag);
    } else {
      setForm(createInitialForm());
      setFormMode('create');
      setEditingFlag(null);
    }

    setFormErrors({});
    setSuccessMessage('');
    if (!isControlled) {
      setError('');
    }
    setIsModalOpen(true);
  };

  const handleViewFlag = (flagKey) => {
    navigate(`/flags/${flagKey}`);
  };

  const handleDeleteFlag = async (flagKey) => {
    const confirmed = window.confirm(`Delete feature flag '${flagKey}'? This action cannot be undone.`);
    if (!confirmed) {
      return;
    }

    try {
      await deleteFlag(flagKey);
      setSuccessMessage(`Flag '${flagKey}' deleted successfully.`);
      await loadFlags();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to delete feature flag.';
      console.error('Delete feature flag failed:', err);
      setError(message);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setForm(createInitialForm());
    setFormErrors({});
    setFormMode('create');
    setEditingFlag(null);
  };

  const handleFieldChange = (event) => {
    const { name, value, type: inputType, checked } = event.target;
    const nextValue = inputType === 'checkbox' ? checked : value;

    setForm((current) => ({
      ...current,
      [name]: name === 'environment_id' || name === 'rollout_percentage' ? Number(nextValue) : nextValue,
    }));
  };

  const validateForm = () => {
    const validationErrors = {};

    if (!form.key.trim()) {
      validationErrors.key = 'Feature key is required.';
    }

    if (!form.owner_team.trim()) {
      validationErrors.owner_team = 'Owner team is required.';
    }

    if (!form.description.trim()) {
      validationErrors.description = 'Description is required.';
    }

    return validationErrors;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    try {
      setSubmitting(true);
      setError('');
      setSuccessMessage('');

      const payload = {
        key: form.key.trim(),
        type: 'boolean',
        default_value: form.default_value,
        enabled: form.enabled,
        rollout_percentage: Number(form.rollout_percentage ?? 0),
        description: form.description.trim(),
        owner_team: form.owner_team.trim(),
        environment_id: form.environment_id,
        target_users: form.target_users || [],
      };

      if (formMode === 'edit' && editingFlag) {
        await updateFlag(editingFlag.key, payload);
        setSuccessMessage(`Flag '${payload.key}' updated successfully.`);
      } else {
        await createFlag(payload);
        setSuccessMessage(`Flag '${payload.key}' created successfully.`);
      }

      await loadFlags();
      handleCloseModal();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to create feature flag.';
      console.error('Feature flag submit failed:', err);
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.headerRow}>
          <div>
            <h2 style={styles.title}>Feature Flag Management</h2>
            <p style={styles.subtitle}>Manage rollout status and ownership for your feature flags.</p>
          </div>
          <button type="button" style={styles.primaryButton} onClick={() => handleOpenModal()}>
            Create Flag
          </button>
        </div>

        {successMessage ? <p style={styles.success}>{successMessage}</p> : null}
        {!isControlled && currentError ? <p style={styles.error}>{currentError}</p> : null}

        {currentLoading ? (
          <div style={styles.loadingState}>
            <span style={styles.spinner} aria-label="Loading" />
            <span>Loading feature flags...</span>
          </div>
        ) : flags.length === 0 ? (
          <p style={styles.message}>No feature flags found. Create one to get started.</p>
        ) : (
          <div style={styles.tableWrapper}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>Flag Key</th>
                  <th style={styles.th}>Type</th>
                  <th style={styles.th}>Status</th>
                  <th style={styles.th}>Owner Team</th>
                  <th style={styles.th}>Environment</th>
                  <th style={styles.th}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {flags.map((flag) => (
                  <tr key={flag.id}>
                    <td style={styles.td}>{flag.key}</td>
                    <td style={styles.td}>{flag.type}</td>
                    <td style={styles.td}>
                      <span style={flag.enabled ? styles.enabled : styles.disabled}>
                        {flag.enabled ? '🟢 Enabled' : '🔴 Disabled'}
                      </span>
                    </td>
                    <td style={styles.td}>{flag.owner_team}</td>
                    <td style={styles.td}>{environmentOptions.find((option) => option.value === flag.environment_id)?.label || flag.environment_id}</td>
                    <td style={styles.td}>
                      <button type="button" style={styles.linkButton} onClick={() => handleViewFlag(flag.key)}>
                        View
                      </button>
                      <button type="button" style={styles.editButton} onClick={() => handleOpenModal(flag)}>
                        Edit
                      </button>
                      <button type="button" style={styles.deleteButton} onClick={() => handleDeleteFlag(flag.key)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <FeatureFlagForm
        isOpen={isModalOpen}
        form={form}
        formErrors={formErrors}
        submitting={submitting}
        environmentOptions={environmentOptions}
        onClose={handleCloseModal}
        onChange={handleFieldChange}
        onSubmit={handleSubmit}
        onDefaultValueChange={(event) =>
          setForm((current) => ({ ...current, default_value: event.target.value === 'true' }))
        }
        title={formMode === 'edit' ? 'Edit Feature Flag' : 'Create Feature Flag'}
        submitLabel={formMode === 'edit' ? 'Save Changes' : 'Create Flag'}
      />
    </div>
  );
}

const styles = {
  page: {
    minHeight: '100vh',
    background: '#f3f4f6',
    padding: '24px',
    fontFamily: 'Arial, sans-serif',
  },
  card: {
    maxWidth: '980px',
    margin: '0 auto',
    background: '#ffffff',
    borderRadius: '12px',
    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
    padding: '24px',
  },
  headerRow: {
    marginBottom: '20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '16px',
  },
  title: {
    margin: 0,
    fontSize: '24px',
    color: '#111827',
  },
  subtitle: {
    margin: '6px 0 0',
    color: '#6b7280',
    fontSize: '14px',
  },
  primaryButton: {
    border: 'none',
    borderRadius: '8px',
    padding: '10px 16px',
    background: '#2563eb',
    color: '#ffffff',
    cursor: 'pointer',
    fontWeight: 600,
  },
  secondaryButton: {
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    padding: '10px 16px',
    background: '#ffffff',
    color: '#374151',
    cursor: 'pointer',
    fontWeight: 600,
  },
  tableWrapper: {
    overflowX: 'auto',
  },
  loadingState: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    color: '#4b5563',
    fontSize: '14px',
    padding: '12px 0',
  },
  spinner: {
    width: '16px',
    height: '16px',
    border: '2px solid #dbeafe',
    borderTopColor: '#2563eb',
    borderRadius: '50%',
    display: 'inline-block',
    animation: 'spin 0.8s linear infinite',
  },
  message: {
    margin: 0,
    color: '#4b5563',
    fontSize: '14px',
  },
  success: {
    margin: '0 0 12px',
    color: '#166534',
    fontSize: '14px',
    fontWeight: 600,
  },
  error: {
    margin: '0 0 12px',
    color: '#b91c1c',
    fontSize: '14px',
    fontWeight: 600,
  },
  enabled: {
    display: 'inline-flex',
    alignItems: 'center',
    borderRadius: '999px',
    background: '#dcfce7',
    color: '#166534',
    padding: '6px 10px',
    fontWeight: 600,
  },
  disabled: {
    display: 'inline-flex',
    alignItems: 'center',
    borderRadius: '999px',
    background: '#fee2e2',
    color: '#991b1b',
    padding: '6px 10px',
    fontWeight: 600,
  },
  th: {
    textAlign: 'left',
    padding: '12px 10px',
    borderBottom: '1px solid #e5e7eb',
    color: '#374151',
    fontSize: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  td: {
    padding: '12px 10px',
    borderBottom: '1px solid #f1f5f9',
    color: '#111827',
    fontSize: '14px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  linkButton: {
    border: 'none',
    background: 'transparent',
    color: '#2563eb',
    cursor: 'pointer',
    fontWeight: 600,
    marginRight: '8px',
  },
  editButton: {
    border: 'none',
    background: '#dbeafe',
    color: '#1d4ed8',
    borderRadius: '6px',
    padding: '6px 10px',
    cursor: 'pointer',
    fontWeight: 600,
    marginRight: '8px',
  },
  deleteButton: {
    border: 'none',
    background: '#fee2e2',
    color: '#b91c1c',
    borderRadius: '6px',
    padding: '6px 10px',
    cursor: 'pointer',
    fontWeight: 600,
  },
};

export default FeatureFlags;
