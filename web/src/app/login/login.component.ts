import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthenticatedUser, UserPreferences } from '../models/auth.models';
import { AuthService } from '../services/auth.service';
import { SessionService } from '../session/session.service';
import { getApiErrorMessage } from '../utils/api-error';

const LOGIN_CLIENT = 'angular-workshop';
const DEFAULT_PREFERENCES: UserPreferences = { theme: 'light', showTips: true, compact: false };

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  username = '';
  password = '';
  busy = false;
  message = '';
  preferences: UserPreferences = { ...DEFAULT_PREFERENCES };

  constructor(
    private readonly authService: AuthService,
    private readonly sessionService: SessionService,
    private readonly router: Router
  ) {
    try {
      this.preferences = { ...DEFAULT_PREFERENCES, ...this.sessionService.getPreferences() };
    } catch (error) {
      console.log('Preferences could not be loaded', error);
    }
  }

  async login(): Promise<void> {
    this.message = '';
    if (!this.username.trim()) {
      this.message = 'Ingrese un usuario.';
      return;
    }
    if (!this.password.trim()) {
      this.message = 'Ingrese una contraseña.';
      return;
    }

    this.busy = true;
    try {
      const response = await this.authService.login({
        username: this.username,
        password: this.password,
        client: LOGIN_CLIENT
      });
      if (!response.token || !response.user) {
        this.message = 'El backend respondió sin token.';
        return;
      }
      this.sessionService.saveSession(response.token, response.user, this.preferences);
      await this.router.navigate(['/dashboard']);
    } catch (error: unknown) {
      this.message = getApiErrorMessage(error, 'No se pudo autenticar.');
      console.error(error);
    } finally {
      this.busy = false;
    }
  }
}
