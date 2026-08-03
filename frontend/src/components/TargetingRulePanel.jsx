import React, { useState } from 'react';

const TargetingRulePanel = ({ users = [], groups = [], onChange, onSave }) => {
  const [localUsers, setLocalUsers] = useState(Array.isArray(users) ? users : []);
  const [localGroups, setLocalGroups] = useState(Array.isArray(groups) ? groups : []);
  const [input, setInput] = useState('');
  const [groupInput, setGroupInput] = useState('');

  const handleAdd = () => {
    const v = input.trim();
    if (!v) return;
    if (localUsers.includes(v)) {
      setInput('');
      return;
    }
    const next = [...localUsers, v];
    setLocalUsers(next);
    setInput('');
    if (onChange) onChange(next);
  };

  const handleRemove = (id) => {
    const next = localUsers.filter((u) => u !== id);
    setLocalUsers(next);
    if (onChange) onChange(next);
  };

  const handleAddGroup = () => {
    const v = groupInput.trim();
    if (!v) return;
    if (localGroups.includes(v)) {
      setGroupInput('');
      return;
    }
    const next = [...localGroups, v];
    setLocalGroups(next);
    setGroupInput('');
    if (onChange) onChange(localUsers, next);
  };

  const handleRemoveGroup = (name) => {
    const next = localGroups.filter((g) => g !== name);
    setLocalGroups(next);
    if (onChange) onChange(localUsers, next);
  };

  return (
    <div style={styles.panel}>
      <h4 style={styles.title}>User Targeting</h4>
      <p style={styles.hint}>Whitelisted user IDs that will always receive this feature.</p>

      <div style={styles.inputRow}>
        <input
          placeholder="user-123"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={styles.input}
        />
        <button type="button" style={styles.addButton} onClick={handleAdd}>
          Add
        </button>
      </div>

      <div style={{ display: 'grid', gap: '12px' }}>
        <div>
          <strong style={{ display: 'block', marginBottom: 8 }}>Target Groups</strong>
          <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <input
              placeholder="beta_users"
              value={groupInput}
              onChange={(e) => setGroupInput(e.target.value)}
              style={styles.input}
            />
            <button type="button" style={styles.addButton} onClick={handleAddGroup}>
              Add Group
            </button>
          </div>

          <ul style={styles.list}>
            {localGroups.length === 0 ? (
              <li style={styles.empty}>No groups targeted.</li>
            ) : (
              localGroups.map((g) => (
                <li key={g} style={styles.listItem}>
                  <span style={styles.userId}>✓ {g}</span>
                  <button type="button" style={styles.removeButton} onClick={() => handleRemoveGroup(g)}>
                    Remove
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>

        <div>
          <strong style={{ display: 'block', marginBottom: 8 }}>Target Users</strong>
          <ul style={styles.list}>
            {localUsers.length === 0 ? (
              <li style={styles.empty}>No users targeted.</li>
            ) : (
              localUsers.map((u) => (
                <li key={u} style={styles.listItem}>
                  <span style={styles.userId}>{u}</span>
                  <button type="button" style={styles.removeButton} onClick={() => handleRemove(u)}>
                    Remove
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      </div>

      <div style={styles.actions}>
        <button
          type="button"
          style={styles.saveButton}
          onClick={() => onSave && onSave(localUsers, localGroups)}
        >
          Save Targeting
        </button>
      </div>
    </div>
  );
};

const styles = {
  panel: {
    padding: '16px',
    borderRadius: '8px',
    background: '#ffffff',
    border: '1px solid #e6edf3',
  },
  title: { margin: 0, fontSize: '16px', color: '#111827' },
  hint: { margin: '6px 0 12px', color: '#6b7280', fontSize: '13px' },
  inputRow: { display: 'flex', gap: '8px', marginBottom: '12px' },
  input: { flex: 1, padding: '8px 10px', borderRadius: '8px', border: '1px solid #d1d5db' },
  addButton: { padding: '8px 12px', borderRadius: '8px', background: '#2563eb', color: '#fff', border: 'none' },
  list: { listStyle: 'none', padding: 0, margin: 0 },
  empty: { color: '#6b7280' },
  listItem: { display: 'flex', justifyContent: 'space-between', gap: '8px', padding: '8px 0', borderBottom: '1px solid #f1f5f9' },
  userId: { color: '#111827' },
  removeButton: { border: 'none', background: '#fee2e2', color: '#b91c1c', borderRadius: '6px', padding: '6px 10px' },
  actions: { marginTop: '12px', display: 'flex', justifyContent: 'flex-end' },
  saveButton: { border: 'none', background: '#10b981', color: '#fff', padding: '8px 12px', borderRadius: '8px' },
};

export default TargetingRulePanel;
