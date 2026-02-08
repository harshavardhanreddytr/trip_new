import { useState, useEffect } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/app/components/ui/sheet";
import { Button } from "@/app/components/ui/button";
import { Textarea } from "@/app/components/ui/textarea";
import { Save } from "lucide-react";
import { toast } from "sonner";

interface NotesSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  taskTitle: string;
  notes: string;
  onSave: (notes: string) => void;
}

export function NotesSheet({
  open,
  onOpenChange,
  taskTitle,
  notes,
  onSave,
}: NotesSheetProps) {
  const [localNotes, setLocalNotes] = useState(notes);
  const [autoSaving, setAutoSaving] = useState(false);

  useEffect(() => {
    setLocalNotes(notes);
  }, [notes]);

  // Auto-save after 2 seconds of inactivity
  useEffect(() => {
    if (localNotes === notes) return;

    setAutoSaving(true);
    const timer = setTimeout(() => {
      onSave(localNotes);
      setAutoSaving(false);
    }, 2000);

    return () => clearTimeout(timer);
  }, [localNotes, notes, onSave]);

  const handleSave = () => {
    onSave(localNotes);
    toast.success("Notes saved");
    onOpenChange(false);
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="h-[80vh] sm:h-[60vh]">
        <SheetHeader>
          <SheetTitle>{taskTitle}</SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-sm text-[var(--warm-gray)]">Notes</label>
            {autoSaving && (
              <span className="text-xs text-[var(--olive-green)] animate-pulse">
                Auto-saving...
              </span>
            )}
          </div>

          <Textarea
            value={localNotes}
            onChange={(e) => setLocalNotes(e.target.value)}
            placeholder="Add your notes here..."
            className="min-h-[200px] resize-none bg-white"
          />

          <Button
            onClick={handleSave}
            className="w-full bg-[var(--olive-green)] hover:bg-[var(--olive-green-light)]"
          >
            <Save className="h-4 w-4 mr-2" />
            Save & Close
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
