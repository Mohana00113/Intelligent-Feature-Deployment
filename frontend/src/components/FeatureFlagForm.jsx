const FeatureFlagForm = ({
  isOpen,
  form,
  formErrors,
  submitting,
  environmentOptions,
  onClose,
  onChange,
  onSubmit,
  onDefaultValueChange,
  title = 'Create Feature Flag',
  submitLabel = 'Create Flag',
}) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div style={styles.modalOverlay} role="dialog" aria-modal="true">
      <div style={styles.modalCard}>
        <div style={styles.modalHeader}>
          <h3 style={styles.modalTitle}>{title}</h3>
          <button type="button" style={styles.closeButton} onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={onSubmit} style={styles.form}>
          <label style={styles.field}>
            <span style={styles.label}>Feature Key</span>
            <input
              name="key"
              value={form.key}
              onChange={onChange}
              style={styles.input}
              placeholder="new_dashboard"
            />
            {formErrors.key ? <span style={styles.fieldError}>{formErrors.key}</span> : null}
          </label>

          <label style={styles.field}>
            <span style={styles.label}>Feature Type</span>
            <select name="type" value={form.type} onChange={onChange} style={styles.input} disabled>
              <option value="boolean">Boolean</option>
            </select>
          </label>

          <label style={styles.field}>
            <span style={styles.label}>Default Value</span>
            <select
              name="default_value"
              value={String(form.default_value)}
              onChange={onDefaultValueChange}
              style={styles.input}
            >
              <option value="true">True</option>
              <option value="false">False</option>
            </select>
          </label>

          <label style={styles.field}>
            <span style={styles.label}>Description</span>
            <textarea
              name="description"
              value={form.description}
              onChange={onChange}
              style={{ ...styles.input, minHeight: '88px', resize: 'vertical' }}
              placeholder="Describe the flag and rollout intent"
            />
            {formErrors.description ? <span style={styles.fieldError}>{formErrors.description}</span> : null}
          </label>

          <label style={styles.field}>
            <span style={styles.label}>Owner Team</span>
            <input
              name="owner_team"
              value={form.owner_team}
              onChange={onChange}
              style={styles.input}
              placeholder="Platform"
            />
            {formErrors.owner_team ? <span style={styles.fieldError}>{formErrors.owner_team}</span> : null}
          </label>

          <label style={styles.field}>
            <span style={styles.label}>Environment</span>
            <select name="environment_id" value={form.environment_id} onChange={onChange} style={styles.input}>
              {environmentOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <div style={styles.rolloutSection}>
            <label htmlFor="rollout_percentage" style={styles.label}>Percentage Rollout</label>
            <div style={styles.rolloutRow}>
              <input
                id="rollout_percentage"
                name="rollout_percentage"
                type="range"
                min="0"
                max="100"
                step="1"
                value={Number(form.rollout_percentage ?? 0)}
                onChange={onChange}
                style={styles.rangeInput}
                aria-label="Percentage Rollout"
              />
              <span style={styles.rolloutValue}>{Number(form.rollout_percentage ?? 0)}%</span>
            </div>
            <p style={styles.rolloutText}>Enabled for {Number(form.rollout_percentage ?? 0)}% of users.</p>
          </div>

          <label style={{ ...styles.field, flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
            <input name="enabled" type="checkbox" checked={form.enabled} onChange={onChange} />
            <span style={styles.label}>Enabled Toggle</span>
          </label>

          <div style={styles.modalActions}>
            <button type="button" style={styles.secondaryButton} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" style={styles.primaryButton} disabled={submitting}>
              {submitting ? (submitLabel === 'Save Changes' ? 'Saving...' : 'Creating...') : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const styles = {
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
  rolloutSection: {
    display: 'grid',
    gap: '8px',
    padding: '10px 0',
  },
  rolloutRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  rangeInput: {
    flex: 1,
    accentColor: '#2563eb',
  },
  rolloutValue: {
    minWidth: '56px',
    textAlign: 'right',
    fontWeight: 700,
    color: '#111827',
  },
  rolloutText: {
    margin: 0,
    color: '#475569',
    fontSize: '13px',
  },
  modalActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '10px',
    marginTop: '8px',
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
  primaryButton: {
    border: 'none',
    borderRadius: '8px',
    padding: '10px 16px',
    background: '#2563eb',
    color: '#ffffff',
    cursor: 'pointer',
    fontWeight: 600,
  },
};

export default FeatureFlagForm;
