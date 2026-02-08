import { UserAvatar } from '@/app/components/UserAvatar';
import { Check, X } from 'lucide-react';

interface PendingRequestCardProps {
  name: string;
  memberId: string;
  onAccept: () => void;
  onReject: () => void;
}

export function PendingRequestCard({
  name,
  memberId,
  onAccept,
  onReject,
}: PendingRequestCardProps) {
  return (
    <div className="bg-card rounded-xl p-4 shadow-sm border border-border flex items-center gap-4 hover:shadow-md transition-shadow">
      <UserAvatar name={name} size="md" />
      <div className="flex-1 min-w-0">
        <h4 className="text-card-foreground truncate">{name}</h4>
        <p className="text-xs text-muted-foreground mt-0.5">{memberId}</p>
      </div>
      <div className="flex gap-2">
        <button
          onClick={onAccept}
          className="p-2.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Check className="w-4 h-4" />
        </button>
        <button
          onClick={onReject}
          className="p-2.5 rounded-lg bg-secondary text-secondary-foreground hover:bg-accent transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
