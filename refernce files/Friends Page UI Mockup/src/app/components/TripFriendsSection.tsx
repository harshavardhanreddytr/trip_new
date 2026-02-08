import { UserAvatar } from '@/app/components/UserAvatar';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';

interface TripFriend {
  name: string;
  memberId: string;
}

interface TripFriendsSectionProps {
  tripName: string;
  friends: TripFriend[];
}

export function TripFriendsSection({ tripName, friends }: TripFriendsSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-card rounded-xl shadow-sm border border-border overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-5 py-4 flex items-center justify-between hover:bg-secondary/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-primary" />
            ) : (
              <ChevronRight className="w-4 h-4 text-primary" />
            )}
          </div>
          <div className="text-left">
            <h4 className="text-card-foreground">{tripName}</h4>
            <p className="text-xs text-muted-foreground mt-0.5">
              {friends.length} {friends.length === 1 ? 'friend' : 'friends'}
            </p>
          </div>
        </div>
        <div className="flex -space-x-2">
          {friends.slice(0, 3).map((friend, idx) => (
            <div key={idx} className="ring-2 ring-card rounded-full">
              <UserAvatar name={friend.name} size="sm" />
            </div>
          ))}
          {friends.length > 3 && (
            <div className="w-10 h-10 rounded-full bg-secondary ring-2 ring-card flex items-center justify-center text-xs font-medium text-muted-foreground">
              +{friends.length - 3}
            </div>
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="px-5 pb-4 pt-1 space-y-3 border-t border-border bg-secondary/20">
          {friends.map((friend, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 bg-card rounded-lg">
              <UserAvatar name={friend.name} size="sm" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-card-foreground truncate">
                  {friend.name}
                </p>
                <p className="text-xs text-muted-foreground">{friend.memberId}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
