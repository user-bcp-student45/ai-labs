import '@angular/compiler';
import { readFileSync } from 'node:fs';
import { Router } from '@angular/router';
import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthService } from '../services/auth.service';
import { SessionService } from '../session/session.service';
import { LoginComponent } from './login.component';

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

describe('LoginComponent characterization', () => {
  let router: { navigate: ReturnType<typeof vi.fn> };
  let sessionService: SessionService;

  beforeEach(() => {
    storedValues.clear();
    vi.clearAllMocks();
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: localStorageMock
    });
    router = { navigate: vi.fn().mockResolvedValue(true) };
    sessionService = new SessionService();
  });

  it('posts the observed login contract and persists the returned session', async () => {
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'fake-token', user: { username: 'student' } }
    } as Awaited<ReturnType<typeof axios.post>>);
    const component = new LoginComponent(new AuthService(), sessionService, router as unknown as Router);
    component.username = 'student';
    component.password = 'fake-password';

    await component.login();

    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'fake-password', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(localStorageMock.getItem('workshop_token')).toBe('fake-token');
    expect(localStorageMock.getItem('workshop_user')).toBe('{"username":"student"}');
    expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
    expect(component.busy).toBe(false);
  });

  it('loads saved preferences over the defaults', () => {
    storedValues.set('workshop_preferences', '{"theme":"dark"}');

    const component = new LoginComponent(new AuthService(), sessionService, router as unknown as Router);

    expect(component.preferences).toEqual({ theme: 'dark', showTips: true, compact: false });
  });

  it('rejects missing credentials without making a request', async () => {
    const component = new LoginComponent(new AuthService(), sessionService, router as unknown as Router);

    await component.login();
    expect(component.message).toContain('Ingrese un usuario.');

    component.username = 'student';
    await component.login();
    expect(component.message).toContain('Ingrese una contraseña.');
    expect(axios.post).not.toHaveBeenCalled();
  });

  it('reports a response without a token and does not navigate', async () => {
    vi.mocked(axios.post).mockResolvedValue({ data: {} } as Awaited<ReturnType<typeof axios.post>>);
    const component = new LoginComponent(new AuthService(), sessionService, router as unknown as Router);
    component.username = 'student';
    component.password = 'fake-password';

    await component.login();

    expect(component.message).toContain('El backend respondió sin token.');
    expect(router.navigate).not.toHaveBeenCalled();
    expect(component.busy).toBe(false);
  });

  it('shows a generic message for a failed login', async () => {
    vi.mocked(axios.post).mockRejectedValue({ response: { data: { message: 'Login denied' } } });
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const component = new LoginComponent(new AuthService(), sessionService, router as unknown as Router);
    component.username = 'student';
    component.password = 'fake-password';

    await component.login();

    expect(component.message).toBe('No se pudo autenticar.');
    expect(component.message).not.toContain('Login denied');
    expect(router.navigate).not.toHaveBeenCalled();
    expect(component.busy).toBe(false);
    errorSpy.mockRestore();
  });

  it('renders the message as escaped text', () => {
    const template = readFileSync(new URL('./login.component.html', import.meta.url), 'utf8');

    expect(template).toContain('{{ message }}');
    expect(template).not.toContain('[innerHTML]');
  });
});