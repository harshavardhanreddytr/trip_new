import { useState } from "react";
import type { Task, TaskStatus, DayContext } from "@/app/components/DayTasksPage";
import { motion } from "motion/react";
import {
  MapPin,
  Navigation,
  Share2,
  MoreVertical,
  StickyNote,
  Check,
  Circle,
  X,
} from "lucide-react";
import { Button } from "@/app/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/app/components/ui/dropdown-menu";
import { NotesSheet } from "@/app/components/NotesSheet";
import { toast } from "sonner";

interface TaskBlockProps {
  task: Task;
  variant: "past" | "current" | "upcoming";
  dayContext: DayContext;
  isFirst: boolean;
  isLast: boolean;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onNotesUpdate: (taskId: string, notes: string) => void;
  onDeleteTask: (taskId: string) => void;
  onAddTask: (referenceId: string, position: "before" | "after") => void;
}

export function TaskBlock({
  task,
  variant,
  dayContext,
  onStatusChange,
  onNotesUpdate,
  onDeleteTask,
  onAddTask,
}: TaskBlockProps) {
  const [notesOpen, setNotesOpen] = useState(false);

  const getDistanceDisplay = () => {
    if (task.distance < 50) {
      return { text: "Nearby", color: "text-[var(--olive-green)]" };
    } else if (task.distance < 1000) {
      return {
        text: `${task.distance}m away`,
        color: "text-[var(--warm-gray)]",
      };
    } else {
      return {
        text: `${(task.distance / 1000).toFixed(1)}km away`,
        color: "text-[var(--warm-gray)]",
      };
    }
  };

  const distance = getDistanceDisplay();

  const getCardStyle = () => {
    const baseStyle = "bg-[var(--beige-card)] border border-[var(--border)] rounded-2xl transition-all duration-300";
    
    switch (variant) {
      case "past":
        return `${baseStyle} opacity-60`;
      case "current":
        return `${baseStyle} ring-2 ring-[var(--olive-green)]/30 shadow-lg shadow-[var(--olive-green)]/10`;
      case "upcoming":
        return `${baseStyle}`;
    }
  };

  const handleStatusClick = (status: TaskStatus) => {
    onStatusChange(task.id, status);
    
    // Show subtle feedback
    if (status === "reached") {
      const now = new Date();
      const timeStr = now.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
      toast.success(`Reached at ${timeStr}`);
    }
  };

  const handleViewMap = () => {
    // Mock implementation
    toast.info(`Opening map for ${task.location.name}`);
  };

  const handleShareLocation = () => {
    // Mock implementation
    toast.success("Location link copied");
  };

  const handleDelete = () => {
    onDeleteTask(task.id);
    toast.success("Task removed");
  };

  const getStatusButton = (status: TaskStatus, icon: React.ReactNode, label: string) => {
    const isActive = task.status === status;
    const baseClass = "flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-2 rounded-lg transition-all duration-200 text-xs sm:text-sm";
    
    if (isActive) {
      return (
        <button
          className={`${baseClass} bg-[var(--olive-green)] text-white`}
          disabled
        >
          {icon}
          <span>{label}</span>
        </button>
      );
    }

    return (
      <button
        onClick={() => handleStatusClick(status)}
        className={`${baseClass} bg-white/50 hover:bg-white text-[var(--foreground)] hover:shadow-sm active:scale-95`}
      >
        {icon}
        <span>{label}</span>
      </button>
    );
  };

  return (
    <motion.div
      id={`task-${task.id}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={getCardStyle()}
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="mb-1 text-[var(--foreground)]">
              {task.title}
            </h3>
            <p className="text-sm text-[var(--warm-gray)]">
              {task.scheduledTime}
            </p>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0 text-[var(--warm-gray)] hover:text-[var(--foreground)]"
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuItem onClick={() => toast.info("Edit task")}>
                Edit task
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAddTask(task.id, "before")}>
                Add task before
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAddTask(task.id, "after")}>
                Add task after
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleDelete} className="text-destructive">
                Delete task
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Location */}
        <div className={`flex items-start gap-3 mb-4 p-3 bg-white/40 rounded-lg ${task.distance < 50 ? 'ring-2 ring-[var(--olive-green)]/20' : ''}`}>
          <MapPin className={`h-5 w-5 mt-0.5 flex-shrink-0 ${task.distance < 50 ? 'text-[var(--olive-green)] animate-pulse' : 'text-[var(--olive-green)]'}`} />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-[var(--foreground)] mb-1">
              {task.location.name}
            </p>
            <p className={`text-xs ${distance.color}`}>
              {distance.text}
            </p>
          </div>
        </div>

        {/* Status reached indicator */}
        {task.reachedAt && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mb-4 p-3 bg-[var(--olive-green)]/10 rounded-lg"
          >
            <p className="text-sm text-[var(--olive-green)]">
              Reached at {task.reachedAt}
            </p>
          </motion.div>
        )}

        {/* Status Actions */}
        {dayContext !== "past" && (
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            {getStatusButton("reached", <Check className="h-4 w-4" />, "Reached")}
            {getStatusButton("pending", <Circle className="h-4 w-4" />, "On the way")}
            {getStatusButton("skipped", <X className="h-4 w-4" />, "Skipped")}
          </div>
        )}

        {/* Actions Row */}
        <div className="flex items-center gap-2 pt-4 border-t border-[var(--border)]">
          <Button
            variant="outline"
            size="sm"
            onClick={handleViewMap}
            className="flex-1 bg-white/50 hover:bg-white"
          >
            <Navigation className="h-4 w-4 mr-2" />
            View on Map
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleShareLocation}
            className="bg-white/50 hover:bg-white"
          >
            <Share2 className="h-4 w-4" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setNotesOpen(true)}
            className="bg-white/50 hover:bg-white relative"
          >
            <StickyNote className="h-4 w-4" />
            {task.notes && (
              <span className="absolute -top-1 -right-1 h-2 w-2 bg-[var(--olive-green)] rounded-full" />
            )}
          </Button>
        </div>
      </div>

      <NotesSheet
        open={notesOpen}
        onOpenChange={setNotesOpen}
        taskTitle={task.title}
        notes={task.notes || ""}
        onSave={(notes) => onNotesUpdate(task.id, notes)}
      />
    </motion.div>
  );
}