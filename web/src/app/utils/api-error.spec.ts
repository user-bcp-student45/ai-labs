import { describe, expect, it } from 'vitest';
import { getApiErrorMessage } from './api-error';

describe('getApiErrorMessage', () => {
  it('does not expose backend details or exceptions to the user', () => {
    expect(getApiErrorMessage({ response: { data: { message: 'Internal server detail' } } }, 'Fallback'))
      .toBe('Fallback');
    expect(getApiErrorMessage(new Error('Network detail'), 'Generic error')).toBe('Generic error');
  });
});