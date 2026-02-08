import { useState, useEffect } from "react";
import { DayHeader } from "@/app/components/DayHeader";
import { ContextBanner } from "@/app/components/ContextBanner";
import { TaskStream } from "@/app/components/TaskStream";
import { FloatingActionBar } from "@/app/components/FloatingActionBar";

/**
 * TripPlanner - Day Tasks Page
 * 
 * A calm, premium travel planner that shows tasks for a single day.
 * 
 * Key Features:
 * - Auto-reach when within 50m of location (simulated)
 * - Status tracking: Reached / On the way / Skipped
 * - Location-aware distance display
 * - Notes with auto-save
 * - Context-aware UI (Today / Past / Upcoming)
 * - No harsh judgments - human-friendly UX
 * - Timestamped interactions for analytics
 * - Mobile-first responsive design
 */

export type TaskStatus = "pending" | "reached" | "skipped";

export type DayContext = "today" | "past" | "upcoming";

export interface Task {
  id: string;
  title: string;
  scheduledTime: string;
  location: {
    name: string;
    lat: number;
    lng: number;
  };
  distance: number; // in meters
  status: TaskStatus;
  reachedAt?: string;
  notes?: string;
}

// Mock data for the day
const MOCK_TASKS: Task[] = [
  {
    id: "1",
    title: "Morning coffee at local café",
    scheduledTime: "08:30 AM",
    location: {
      name: "Café Soleil",
      lat: 48.8566,
      lng: 2.3522,
    },
    distance: 45, // Close enough to auto-reach
    status: "pending",
    notes: "Try their croissants!",
  },
  {
    id: "2",
    title: "Visit Louvre Museum",
    scheduledTime: "10:00 AM",
    location: {
      name: "Louvre Museum",
      lat: 48.8606,
      lng: 2.3376,
    },
    distance: 1200,
    status: "pending",
    notes: "Pre-booked tickets. Don't forget to see Mona Lisa.",
  },
  {
    id: "3",
    title: "Lunch at Le Marais",
    scheduledTime: "01:00 PM",
    location: {
      name: "L'As du Fallafel",
      lat: 48.8575,
      lng: 2.3598,
    },
    distance: 3500,
    status: "pending",
  },
  {
    id: "4",
    title: "Seine River walk",
    scheduledTime: "03:30 PM",
    location: {
      name: "Pont des Arts",
      lat: 48.8583,
      lng: 2.3375,
    },
    distance: 5200,
    status: "pending",
    notes: "Great spot for photos",
  },
  {
    id: "5",
    title: "Dinner reservation",
    scheduledTime: "07:30 PM",
    location: {
      name: "Le Comptoir du Relais",
      lat: 48.8518,
      lng: 2.3392,
    },
    distance: 8900,
    status: "pending",
  },
];

export function DayTasksPage() {
  const [tasks, setTasks] = useState<Task[]>(MOCK_TASKS);
  const [dayContext] = useState<DayContext>("today"); // Can be changed to test different views
  const [showFloating, setShowFloating] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);

  // Simulate geolocation checking
  useEffect(() => {
    const checkProximity = () => {
      setTasks((prevTasks) =>
        prevTasks.map((task) => {
          // Auto-reach if within 50m and not already marked
          if (task.distance < 50 && task.status === "pending") {
            const now = new Date();
            const timeStr = now.toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
            });
            return {
              ...task,
              status: "reached" as TaskStatus,
              reachedAt: timeStr,
            };
          }
          return task;
        })
      );
    };

    // Check proximity every 10 seconds (in real app, use actual geolocation)
    const interval = setInterval(checkProximity, 10000);
    checkProximity(); // Check immediately

    return () => clearInterval(interval);
  }, []);

  // Find current task (next pending task)
  useEffect(() => {
    const nextTask = tasks.find((t) => t.status === "pending");
    setCurrentTaskId(nextTask?.id || null);
  }, [tasks]);

  // Handle scroll to show/hide floating action bar
  useEffect(() => {
    const handleScroll = () => {
      setShowFloating(window.scrollY > 200);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleStatusChange = (taskId: string, status: TaskStatus) => {
    setTasks((prevTasks) =>
      prevTasks.map((task) => {
        if (task.id === taskId) {
          const now = new Date();
          const timeStr = now.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
          });
          return {
            ...task,
            status,
            reachedAt: status === "reached" ? timeStr : undefined,
          };
        }
        return task;
      })
    );
  };

  const handleNotesUpdate = (taskId: string, notes: string) => {
    setTasks((prevTasks) =>
      prevTasks.map((task) => (task.id === taskId ? { ...task, notes } : task))
    );
  };

  const handleDeleteTask = (taskId: string) => {
    setTasks((prevTasks) => prevTasks.filter((task) => task.id !== taskId));
  };

  const handleAddTask = (referenceId: string, position: "before" | "after") => {
    // Mock implementation - in real app, would open a form
    console.log(`Add task ${position} task ${referenceId}`);
  };

  const scrollToCurrentTask = () => {
    if (currentTaskId) {
      const element = document.getElementById(`task-${currentTaskId}`);
      element?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  return (
    <div className="min-h-screen bg-[var(--off-white)] pb-32">
      <div className="max-w-2xl mx-auto px-4 sm:px-0">
        <DayHeader
          date={new Date()}
          dayContext={dayContext}
          taskCount={tasks.length}
        />
        
        <ContextBanner dayContext={dayContext} />
        
        <TaskStream
          tasks={tasks}
          currentTaskId={currentTaskId}
          dayContext={dayContext}
          onStatusChange={handleStatusChange}
          onNotesUpdate={handleNotesUpdate}
          onDeleteTask={handleDeleteTask}
          onAddTask={handleAddTask}
        />
        
        <FloatingActionBar
          visible={showFloating}
          onAddTask={() => console.log("Add task")}
          onJumpToCurrent={scrollToCurrentTask}
        />
      </div>
    </div>
  );
}