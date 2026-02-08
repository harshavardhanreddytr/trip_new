import { Search, Send, QrCode, UserPlus } from 'lucide-react';
import { useState } from 'react';
import { FriendCard } from '@/app/components/FriendCard';
import { PendingRequestCard } from '@/app/components/PendingRequestCard';
import { TripFriendsSection } from '@/app/components/TripFriendsSection';

export default function App() {
  const [memberId, setMemberId] = useState('');
  const [activeFilter, setActiveFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  // Mock data
  const pendingRequests = [
    { id: 1, name: 'Sarah Mitchell', memberId: 'SM4892' },
    { id: 2, name: 'James Chen', memberId: 'JC7341' },
    { id: 3, name: 'Emma Rodriguez', memberId: 'ER2156' },
  ];

  const friends = [
    { id: 1, name: 'Alex Turner', memberId: 'AT9012', isOnline: true },
    { id: 2, name: 'Maya Patel', memberId: 'MP4523', isOnline: true },
    { id: 3, name: 'Daniel Kim', memberId: 'DK8734', isOnline: false },
    { id: 4, name: 'Sofia Garcia', memberId: 'SG2341', isOnline: true },
    { id: 5, name: 'Lucas Brown', memberId: 'LB5678', isOnline: false },
    { id: 6, name: 'Olivia Wilson', memberId: 'OW3421', isOnline: true },
  ];

  const tripFriends = [
    {
      tripName: 'Goa Trip',
      friends: [
        { name: 'Alex Turner', memberId: 'AT9012' },
        { name: 'Maya Patel', memberId: 'MP4523' },
        { name: 'Daniel Kim', memberId: 'DK8734' },
      ],
    },
    {
      tripName: 'Mangalore Trip',
      friends: [
        { name: 'Sofia Garcia', memberId: 'SG2341' },
        { name: 'Lucas Brown', memberId: 'LB5678' },
      ],
    },
    {
      tripName: 'Himalayas Adventure',
      friends: [
        { name: 'Alex Turner', memberId: 'AT9012' },
        { name: 'Olivia Wilson', memberId: 'OW3421' },
        { name: 'Maya Patel', memberId: 'MP4523' },
        { name: 'Daniel Kim', memberId: 'DK8734' },
      ],
    },
  ];

  const handleAcceptRequest = (id: number) => {
    console.log('Accepted request:', id);
  };

  const handleRejectRequest = (id: number) => {
    console.log('Rejected request:', id);
  };

  const handleSendRequest = () => {
    if (memberId.trim()) {
      console.log('Sending request to:', memberId);
      setMemberId('');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-foreground mb-2">Friends</h1>
          <p className="text-muted-foreground">People you trust to travel with</p>
        </div>

        {/* Search and Filters */}
        <div className="mb-8 space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search friends"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3.5 bg-card border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
            />
          </div>

          <div className="flex gap-3 flex-wrap">
            {['All', 'Pending', 'Trips'].map((filter) => (
              <button
                key={filter}
                onClick={() => setActiveFilter(filter)}
                className={`px-5 py-2 rounded-full transition-all ${
                  activeFilter === filter
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'bg-card text-card-foreground border border-border hover:bg-secondary'
                }`}
              >
                {filter}
                {filter === 'Pending' && (
                  <span className="ml-2 px-2 py-0.5 rounded-full bg-primary-foreground/20 text-xs">
                    {pendingRequests.length}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Add Friend Section */}
        <div className="mb-8">
          <div className="bg-card rounded-xl p-6 shadow-sm border border-border">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-primary/10">
                <UserPlus className="w-5 h-5 text-primary" />
              </div>
              <h3 className="text-card-foreground">Add Friend</h3>
            </div>
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <input
                  type="text"
                  placeholder="Enter Member ID"
                  value={memberId}
                  onChange={(e) => setMemberId(e.target.value)}
                  className="w-full px-4 py-3 bg-input-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                />
              </div>
              <button
                onClick={handleSendRequest}
                className="px-6 py-3 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 transition-colors flex items-center gap-2 shadow-sm"
              >
                <Send className="w-4 h-4" />
                Send Request
              </button>
              <button className="px-4 py-3 bg-secondary text-secondary-foreground rounded-xl hover:bg-accent transition-colors">
                <QrCode className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Pending Requests */}
        {pendingRequests.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-card-foreground">Pending Requests</h3>
              <span className="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm">
                {pendingRequests.length} new
              </span>
            </div>
            <div className="grid gap-3">
              {pendingRequests.map((request) => (
                <PendingRequestCard
                  key={request.id}
                  name={request.name}
                  memberId={request.memberId}
                  onAccept={() => handleAcceptRequest(request.id)}
                  onReject={() => handleRejectRequest(request.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Your Friends */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-card-foreground">Your Friends</h3>
            <span className="text-sm text-muted-foreground">
              {friends.length} friends
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
            {friends.map((friend) => (
              <FriendCard
                key={friend.id}
                name={friend.name}
                memberId={friend.memberId}
                isOnline={friend.isOnline}
              />
            ))}
          </div>
        </div>

        {/* Trip-Wise Friends */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-card-foreground">Trip-Wise Friends</h3>
            <span className="text-sm text-muted-foreground">
              {tripFriends.length} trips
            </span>
          </div>
          <div className="space-y-3">
            {tripFriends.map((trip, idx) => (
              <TripFriendsSection
                key={idx}
                tripName={trip.tripName}
                friends={trip.friends}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
