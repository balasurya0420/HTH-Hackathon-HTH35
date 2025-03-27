
import React from 'react';
import SidebarMenu from './SidebarMenu';
import '../styles/components.css';

function MemoriesCollectionPage() {
  const memoryPhotos = [
    {
      id: 1,
      imageUrl: '3.jpg',
      description: 'School friends gathering'
    },
    // Add more photos as needed
  ];

  return (
    <div className="memories-collection-container">
      <SidebarMenu />
      
      <div className="memories-content">
        <div className="memories-header">
          <h1 className="memories-title">Memories Collection</h1>
          <p className="memories-subtitle">Click a Photo to explore</p>
        </div>
        
        <div className="memory-photos">
          {memoryPhotos.map(photo => (
            <div key={photo.id} className="memory-photo-container">
              <img 
                src={photo.imageUrl} 
                alt={photo.description} 
                className="memory-photo" 
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default MemoriesCollectionPage;
