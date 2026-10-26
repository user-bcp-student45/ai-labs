import { describe, expect, it } from 'vitest';
import { formatTaskLabel } from './legacy-format';

describe('formatTaskLabel', () => {
  it('formats priority and owner', () => {
    expect(formatTaskLabel({ priority: 'high', owner: 'student' })).toBe('HIGH · STUDENT');
  });

  it('uses defaults for empty priority and owner', () => {
    expect(formatTaskLabel({ priority: '', owner: '' })).toBe('NORMAL · SIN-ASIGNAR');
  });

  it('returns the empty-task label for null or undefined', () => {
    expect(formatTaskLabel(null)).toBe('SIN-DATOS');
    expect(formatTaskLabel(undefined)).toBe('SIN-DATOS');
  });
});
