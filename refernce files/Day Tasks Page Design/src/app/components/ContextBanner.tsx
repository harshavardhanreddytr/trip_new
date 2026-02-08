import type { DayContext } from "@/app/components/DayTasksPage";
import { motion } from "motion/react";

interface ContextBannerProps {
  dayContext: DayContext;
}

export function ContextBanner({ dayContext }: ContextBannerProps) {
  const getContent = () => {
    switch (dayContext) {
      case "today":
        return {
          message: "Focus on what's ahead. We'll track progress quietly.",
          bgColor: "bg-[var(--olive-green)]/5",
          borderColor: "border-l-[var(--olive-green)]",
        };
      case "past":
        return {
          message: "This day has passed. Records are preserved.",
          bgColor: "bg-[var(--warm-gray)]/5",
          borderColor: "border-l-[var(--warm-gray)]",
        };
      case "upcoming":
        return {
          message: "Plans can still be adjusted.",
          bgColor: "bg-[var(--olive-green-subtle)]/10",
          borderColor: "border-l-[var(--olive-green-subtle)]",
        };
    }
  };

  const content = getContent();

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={`mb-8 p-4 rounded-lg border-l-4 ${content.bgColor} ${content.borderColor}`}
    >
      <p className="text-sm text-[var(--foreground)]/70">{content.message}</p>
    </motion.div>
  );
}