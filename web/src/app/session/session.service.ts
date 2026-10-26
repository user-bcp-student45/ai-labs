import { Injectable } from '@angular/core';
import { AuthenticatedUser, UserPreferences } from '../models/auth.models';

const TOKEN_KEY = 'workshop_token';
const USER_KEY = 'workshop_user';
const PREFERENCES_KEY = 'workshop_preferences';

@Injectable({ providedIn: 'root' })
export class SessionService {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  getUser(): AuthenticatedUser {
    return JSON.parse(localStorage.getItem(USER_KEY) || '{}') as AuthenticatedUser;
  }

  getPreferences(): Partial<UserPreferences> {
    return JSON.parse(localStorage.getItem(PREFERENCES_KEY) || '{}') as Partial<UserPreferences>;
  }

  saveSession(token: string, user: AuthenticatedUser, preferences: UserPreferences): void {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    localStorage.setItem(PREFERENCES_KEY, JSON.stringify(preferences));
  }

  clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}