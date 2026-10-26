import '@angular/compiler';
import { ChangeDetectorRef, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SessionService } from '../session/session.service';
import { TasksService } from '../services/tasks.service';
import { DashboardComponent } from './dashboard.component';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}));

const storedValues = new Map<string, string>();
const localStorageMock = {
  getItem: vi.fn((key: string) => storedValues.get(key) ?? null),
  setItem: vi.fn((key: string, value: string) => storedValues.set(key, value)),
  removeItem: vi.fn((key: string) => storedValues.delete(key)),
  clear: vi.fn(() => storedValues.clear())
};

describe('DashboardComponent characterization', () => {
  let router: { navigate: ReturnType<typeof vi.fn> };
  let detectChanges: ReturnType<typeof vi.fn>;
  let component: DashboardComponent;
  let sessionService: SessionService;

  beforeEach(() => {
    storedValues.clear();
    vi.clearAllMocks();
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: localStorageMock
    });
    router = { navigate: vi.fn().mockResolvedValue(true) };
    detectChanges = vi.fn();
    sessionService = new SessionService();
    component = new DashboardComponent(
      router as unknown as Router,
      { detectChanges } as unknown as ChangeDetectorRef,
      { run: (callback: () => void) => callback() } as unknown as NgZone,
      sessionService,
      new TasksService()
    );
  });

  it('redirects to login when there is no stored token', async () => {
    await component.ngOnInit();

    expect(router.navigate).toHaveBeenCalledWith(['/login']);
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('loads tasks with the observed owner query and bearer token', async () => {
    storedValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    const tasks = [
      { id: 1, title: 'Low', priority: 'low', owner: 'student', status: 'TODO' },
      { id: 2, title: 'High', priority: 'high', owner: 'student', status: 'IN_PROGRESS' },
      { id: 3, title: 'Archived', priority: 'urgent', owner: 'student', status: 'ARCHIVED' }
    ];
    vi.mocked(axios.get).mockResolvedValue({ data: tasks } as Awaited<ReturnType<typeof axios.get>>);

    await component.ngOnInit();

    expect(axios.get).toHaveBeenCalledWith('http://localhost:8000/api/tasks?owner=student', {
      headers: { Authorization: 'Bearer fake-token' }
    });
    expect(component.tasks).toEqual(tasks);
    expect(component.visibleTasks.map((task: { title: string }) => task.title)).toEqual(['Low', 'High']);
    expect(component.visibleTasks[0].label).toBe('LOW · STUDENT');
    expect(component.loading).toBe(false);
    expect(detectChanges).toHaveBeenCalledOnce();
  });

  it('surfaces a task request error and stops loading', async () => {
    storedValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    vi.mocked(axios.get).mockRejectedValue({ response: { data: { detail: 'Tasks unavailable' } } });

    await component.ngOnInit();

    expect(component.error).toBe('No se pudo cargar el dashboard.');
    expect(component.loading).toBe(false);
    expect(detectChanges).toHaveBeenCalledOnce();
  });

  it('removes the session and returns to login on logout', async () => {
    storedValues.set('workshop_token', 'fake-token');
    storedValues.set('workshop_user', '{"username":"student"}');
    storedValues.set('workshop_preferences', '{"theme":"dark"}');

    await component.logout();

    expect(localStorageMock.getItem('workshop_token')).toBeNull();
    expect(localStorageMock.getItem('workshop_user')).toBeNull();
    expect(localStorageMock.getItem('workshop_preferences')).toBe('{"theme":"dark"}');
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('maps known statuses and preserves unknown statuses', () => {
    expect(component.statusLabel('todo')).toBe('Por hacer');
    expect(component.statusLabel('custom')).toBe('custom');
  });
});