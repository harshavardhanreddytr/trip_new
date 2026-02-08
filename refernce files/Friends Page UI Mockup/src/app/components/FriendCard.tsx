import { UserAvatar } from '@/app/components/UserAvatar';
import { MoreVertical, UserMinus, Ban } from 'lucide-react';
import { useState } from 'react';

interface FriendCardProps {
  name: string;
  memberId: string;
  isOnline?: boolean;
}

export function FriendCard({ name, memberId, isOnline }: FriendCardProps) {
  const [showActions, setShowActions] = useState(false);

  return (
    <div className="bg-card rounded-xl p-4 shadow-sm border border-border hover:shadow-md transition-shadow relative">
      <div className="flex flex-col items-center gap-3">
        <UserAvatar name={name} size="lg" isOnline={isOnline} />
        <div className="text-center">
          <h4 className="text-card-foreground">{name}</h4>
          <p className="text-xs text-muted-foreground mt-0.5">{memberId}</p>
        </div>
      </div>

      <button
        onClick={() => setShowActions(!showActions)}
        className="absolute top-3 right-3 p-1.5 rounded-lg hover:bg-secondary transition-colors"
      >
        <MoreVertical className="w-4 h-4 text-muted-foreground" />
      </button>

      {showActions && (
        <div className="absolute top-12 right-3 bg-card rounded-lg shadow-lg border border-border overflow-hidden z-10 min-w-[140px]">
          <button className="w-full px-4 py-2.5 text-left text-sm hover:bg-secondary transition-colors flex items-center gap-2 text-foreground">
            <UserMinus className="w-4 h-4" />
            Remove
          </button>
          <button className="w-full px-4 py-2.5 text-left text-sm hover:bg-secondary transition-colors flex items-center gap-2 text-destructive">
            <Ban className="w-4 h-4" />
            Block
          </button>
        </div>
      )}
    </div>
  );
}
