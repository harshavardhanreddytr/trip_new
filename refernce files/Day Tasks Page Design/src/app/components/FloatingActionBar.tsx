import { motion, AnimatePresence } from "motion/react";
import { Plus, Navigation } from "lucide-react";
import { Button } from "@/app/components/ui/button";

interface FloatingActionBarProps {
  visible: boolean;
  onAddTask: () => void;
  onJumpToCurrent: () => void;
}

export function FloatingActionBar({
  visible,
  onAddTask,
  onJumpToCurrent,
}: FloatingActionBarProps) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="fixed bottom-6 sm:bottom-8 left-1/2 -translate-x-1/2 z-50 px-4 w-full max-w-md"
        >
          <div className="bg-white shadow-2xl rounded-full px-3 sm:px-4 py-3 flex items-center gap-2 sm:gap-3 border border-[var(--border)] justify-center">
            <Button
              onClick={onAddTask}
              size="sm"
              className="rounded-full bg-[var(--olive-green)] hover:bg-[var(--olive-green-light)] text-white text-xs sm:text-sm"
            >
              <Plus className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">Add task</span>
            </Button>

            <div className="h-6 w-px bg-[var(--border)]" />

            <Button
              onClick={onJumpToCurrent}
              size="sm"
              variant="ghost"
              className="rounded-full hover:bg-[var(--olive-green)]/10 text-xs sm:text-sm"
            >
              <Navigation className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">Current task</span>
            </Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}