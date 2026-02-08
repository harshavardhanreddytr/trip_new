import type { Task, TaskStatus, DayContext } from "@/app/components/DayTasksPage";
import { TaskBlock } from "@/app/components/TaskBlock";

interface TaskStreamProps {
  tasks: Task[];
  currentTaskId: string | null;
  dayContext: DayContext;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onNotesUpdate: (taskId: string, notes: string) => void;
  onDeleteTask: (taskId: string) => void;
  onAddTask: (referenceId: string, position: "before" | "after") => void;
}

export function TaskStream({
  tasks,
  currentTaskId,
  dayContext,
  onStatusChange,
  onNotesUpdate,
  onDeleteTask,
  onAddTask,
}: TaskStreamProps) {
  const getTaskVariant = (task: Task): "past" | "current" | "upcoming" => {
    if (task.status !== "pending") {
      return "past";
    }
    if (task.id === currentTaskId) {
      return "current";
    }
    return "upcoming";
  };

  return (
    <div className="space-y-6">
      {tasks.map((task, index) => (
        <TaskBlock
          key={task.id}
          task={task}
          variant={getTaskVariant(task)}
          dayContext={dayContext}
          isFirst={index === 0}
          isLast={index === tasks.length - 1}
          onStatusChange={onStatusChange}
          onNotesUpdate={onNotesUpdate}
          onDeleteTask={onDeleteTask}
          onAddTask={onAddTask}
        />
      ))}
    </div>
  );
}