import { expect } from '@playwright/test';

export class DashboardPage {
  constructor(page) {
    this.page = page;
    this.createFlagButton = page.getByRole('button', { name: 'Create Flag' }).first();
    this.totalCard = page.getByText('Total Feature Flags');
    this.enabledCard = page.getByText('Enabled Feature Flags');
    this.disabledCard = page.getByText('Disabled Feature Flags');
    this.emptyState = page.getByText('No feature flags found. Create one to get started.');
    this.loadingState = page.getByText('Loading feature flags...');
    this.errorAlert = page.getByText('Failed to fetch');
  }

  async goto() {
    await this.page.goto('/');
  }

  async waitForDashboardReady() {
    await this.page.waitForLoadState('domcontentloaded');
    await this.page.getByText('Feature Flag Management').waitFor({ state: 'visible' });
  }

  async expectSummaryCardsVisible() {
    await this.totalCard.waitFor({ state: 'visible' });
    await this.enabledCard.waitFor({ state: 'visible' });
    await this.disabledCard.waitFor({ state: 'visible' });
  }

  async expectNoFailedToFetch() {
    await expect(this.errorAlert).toHaveCount(0);
  }

  async openCreateFlagModal() {
    await this.createFlagButton.click();
  }

  async createFlag({ key, description, ownerTeam, environment = 'Development', enabled = true }) {
    const dialog = this.page.getByRole('dialog');

    await dialog.getByLabel('Feature Key').fill(key);
    await dialog.getByLabel('Description').fill(description);
    await dialog.getByLabel('Owner Team').fill(ownerTeam);
    await dialog.getByLabel('Environment').selectOption({ label: environment });

    if (!enabled) {
      await dialog.getByLabel('Enabled Toggle').uncheck();
    }

    await dialog.getByRole('button', { name: 'Create Flag' }).click();
    await this.page.getByText(`Flag '${key}' created successfully.`).waitFor({ state: 'visible' });
    await this.page.waitForTimeout(250);
  }

  async expectFlagVisible(key) {
    await this.page.getByText(key, { exact: true }).waitFor({ state: 'visible' });
  }

  async findFlagRow(key) {
    const rows = this.page.locator('table tbody tr');
    return rows.filter({ hasText: key }).first();
  }

  async editFlag(key, updates) {
    const row = await this.findFlagRow(key);
    await row.getByRole('button', { name: 'Edit' }).click();
    const dialog = this.page.getByRole('dialog');

    if (updates.description) {
      await dialog.getByLabel('Description').fill(updates.description);
    }

    if (updates.ownerTeam) {
      await dialog.getByLabel('Owner Team').fill(updates.ownerTeam);
    }

    if (updates.enabled !== undefined) {
      const toggle = dialog.getByLabel('Enabled Toggle');
      if (updates.enabled) {
        await toggle.check();
      } else {
        await toggle.uncheck();
      }
    }

    await dialog.getByRole('button', { name: 'Save Changes' }).click();
    await this.page.getByText(`Flag '${key}' updated successfully.`).waitFor({ state: 'visible' });
    await this.page.waitForTimeout(250);
  }

  async deleteFlag(key) {
    const row = await this.findFlagRow(key);
    this.page.once('dialog', async (dialog) => {
      await dialog.accept();
    });
    await row.getByRole('button', { name: 'Delete' }).click();
    await this.page.getByText(`Flag '${key}' deleted successfully.`).waitFor({ state: 'visible' });
    await this.page.waitForTimeout(250);
  }

  async expectEmptyState() {
    await this.emptyState.waitFor({ state: 'visible' });
  }

  async getCardValue(label) {
    const labelNode = this.page.getByText(label, { exact: true }).first();
    await labelNode.waitFor({ state: 'visible' });
    return labelNode.locator('xpath=following-sibling::div').textContent();
  }
}
