export interface Task {
  id?: number;
  title: string;
  description?: string;
  priority: string;
  owner?: string;
  status: string;
  label?: string;
}

export type TaskLabelSource = Pick<Task, 'priority' | 'owner'>;