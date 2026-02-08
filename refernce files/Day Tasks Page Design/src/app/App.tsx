import { DayTasksPage } from "@/app/components/DayTasksPage";
import { Toaster } from "@/app/components/ui/sonner";

export default function App() {
  return (
    <div className="size-full">
      <DayTasksPage />
      <Toaster position="top-center" />
    </div>
  );
}
