// //family.js
// import React from 'react';
// import { Link } from 'react-router-dom';
// import './Family.css';

// const Family = () => {
//   return (
//     <div>
//       <div style={{ display: 'flex', gap: '20px', padding: '20px' }}>
//         <Link to="/100" className="family-box">
//           <h2>Monish : Me</h2>
//         </Link>
//         <Link to="/102" className="family-box">
//           <h2>Bavya</h2>
//         </Link>
//         <Link to="/101" className="family-box">
//           <h2>Harris</h2>
//         </Link>
//       </div>
//     </div>
//   );
// };


// // const blockStyle = {
// //   textDecoration: 'none',
// //   color: 'black',
// //   padding: '20px',
// //   border: '2px solid black',
// //   borderRadius: '10px',
// //   width: '150px',
// //   textAlign: 'center',
// //   cursor: 'pointer',
// //   backgroundColor: '#f0f0f0',
  
// //   /* 3D Effect */
// //   boxShadow: '4px 4px 10px rgba(0, 0, 0, 0.3)',
// //   transition: 'transform 0.2s, box-shadow 0.2s',

// //   /* Hover Effect */
// //   ':hover': {
// //     transform: 'translateY(-5px)', // Moves box up slightly
// //     boxShadow: '6px 6px 15px rgba(0, 0, 0, 0.4)',
// //   }
// // };

// export default Family;
import React from 'react';
import { Link } from 'react-router-dom';
import './Family.css';

const Family = () => {
  return (
    <div className="family-container">
      <h1 className="title">👨‍👩‍👧‍👦 My Family</h1>
      <div className="family-grid">
        <Link to="/100" className="family-card">
          <img src="/images/image2.jpg" alt="Monish" className="family-image" />
          <div className="family-info">
            <h2>Monish (Me)</h2>
          </div>
        </Link>
        <Link to="/102" className="family-card">
          <img src="/images/image3.jpg" alt="Bavya" className="family-image" />
          <div className="family-info">
            <h2>Bavya</h2>
          </div>
        </Link>
        <Link to="/101" className="family-card">
          <img src="/images/image1.jpg" alt="Harris" className="family-image" />
          <div className="family-info">
            <h2>Harris</h2>
          </div>
        </Link>
      </div>
    </div>
  );
};

export default Family;
