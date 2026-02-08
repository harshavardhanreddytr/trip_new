import type { DayContext } from "@/app/components/DayTasksPage";

interface DayHeaderProps {
  date: Date;
  dayContext: DayContext;
  taskCount: number;
}

export function DayHeader({ date, dayContext, taskCount }: DayHeaderProps) {
  const dayOfWeek = date.toLocaleDateString("en-US", { weekday: "long" });
  const dayDate = date.toLocaleDateString("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  const getContextLabel = () => {
    switch (dayContext) {
      case "today":
        return "Today";
      case "past":
        return "Past Day";
      case "upcoming":
        return "Upcoming Day";
    }
  };

  const getContextStyle = () => {
    switch (dayContext) {
      case "today":
        return "bg-[var(--olive-green)] text-white";
      case "past":
        return "bg-[var(--warm-gray)]/20 text-[var(--warm-gray)]";
      case "upcoming":
        return "bg-[var(--olive-green-subtle)]/30 text-[var(--olive-green)]";
    }
  };

  const getHeaderOpacity = () => {
    return dayContext === "past" ? "opacity-70" : "opacity-100";
  };

  return (
    <header className={`pt-8 pb-6 ${getHeaderOpacity()} transition-opacity duration-300`}>
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl sm:text-3xl tracking-tight text-[var(--foreground)]">
              {dayOfWeek}
            </h1>
            <span
              className={`px-3 py-1 rounded-full text-xs ${getContextStyle()} transition-colors duration-300`}
            >
              {getContextLabel()}
            </span>
          </div>
          <p className="text-base sm:text-lg text-[var(--warm-gray)]">{dayDate}</p>
        </div>
      </div>

      <p className="text-sm text-[var(--warm-gray)]">
        {taskCount} {taskCount === 1 ? "task" : "tasks"} planned
      </p>
    </header>
  );
}