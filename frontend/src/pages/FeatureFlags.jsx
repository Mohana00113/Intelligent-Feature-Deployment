import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import FeatureFlagForm from '../components/FeatureFlagForm';
import { createFlag, deleteFlag, getFlags, updateFlag } from '../services/api';

const createInitialForm = () => ({
  key: '',
  type: 'boolean',
  default_value: true,
  enabled: true,
  description: '',
  owner_team: '',
  environment_id: 1,
});

function FeatureFlags() {
  const [flags, setFlags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState(createInitialForm);
  const [formErrors, setFormErrors] = useState({});
  const [formMode, setFormMode] = useState('create');
  const navigate = useNavigate();
  const [editingFlag, setEditingFlag] = useState(null);

  const environmentOptions = useMemo(() => [
    { value: 1, label: 'Development' },
    { value: 2, label: 'Staging' },
    { value: 3, label: 'Production' },
  ], []);

  async function loadFlags() {
    try {
      setLoading(true);
      setError('');
      const data = await getFlags();
      setFlags(data);
    } catch (err) {
      setError(err.message || 'Failed to load feature flags.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFlags();
  }, []);

  const handleOpenModal = (flag = null) => {
    if (flag) {
      setForm({
        key: flag.key,
        type: flag.type || 'boolean',
        default_value: Boolean(flag.default_value),
        enabled: flag.enabled ?? true,
        description: flag.description || '',
        owner_team: flag.owner_team || '',
        environment_id: flag.environment_id || 1,
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
    setError('');
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
      setError(err.message || 'Unable to delete feature flag.');
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
      [name]: name === 'environment_id' ? Number(nextValue) : nextValue,
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
        description: form.description.trim(),
        owner_team: form.owner_team.trim(),
        environment_id: form.environment_id,
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
      setError(err.message || 'Unable to create feature flag.');
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
          <button type="button" style={styles.primaryButton} onClick={handleOpenModal}>
            Create Flag
          </button>
        </div>

        {successMessage ? <p style={styles.success}>{successMessage}</p> : null}
        {error ? <p style={styles.error}>{error}</p> : null}

        {loading ? (
          <p style={styles.message}>Loading...</p>
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
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '12px',
    background: '#eef2ff',
    color: '#374151',
    borderBottom: '1px solid #d1d5db',
    fontSize: '14px',
  },
  td: {
    padding: '12px',
    borderBottom: '1px solid #e5e7eb',
    color: '#111827',
    fontSize: '14px',
  },
  enabled: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    color: '#15803d',
    fontWeight: 600,
  },
  disabled: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    color: '#b91c1c',
    fontWeight: 600,
  },
  modalOverlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(17, 24, 39, 0.6)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px',
  },
  modalCard: {
    width: '100%',
    maxWidth: '560px',
    background: '#ffffff',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 20px 45px rgba(0, 0, 0, 0.24)',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  modalTitle: {
    margin: 0,
    fontSize: '20px',
    color: '#111827',
  },
  closeButton: {
    border: 'none',
    background: 'transparent',
    fontSize: '24px',
    color: '#6b7280',
    cursor: 'pointer',
  },
  form: {
    display: 'grid',
    gap: '12px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  label: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#374151',
  },
  input: {
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    padding: '10px 12px',
    fontSize: '14px',
    color: '#111827',
  },
  fieldError: {
    color: '#b91c1c',
    fontSize: '12px',
  },
  modalActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '10px',
    marginTop: '8px',
  },
};

export default FeatureFlags;
