const applicationServerPublicKey = 'BK8L9As8JbPTeHIpia_gaDbBvBXA7bMm_ddSE3qj8N2NvG_wh1ySrZibOSQzY0E-M2oWSgO5nYsQ6mFPt731sAc';

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/\-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function registerServiceWorker() {
  return navigator.serviceWorker.register('https://vestelagu.site/static/js/sw.js')
  .then(function(registration) {
    console.log('Service worker successfully registered.');
    return registration;
  })
  .catch(function(err) {
    console.error('Unable to register service worker.', err);
  });
}

function subscribeUserToPush() {
  return navigator.serviceWorker.register('https://vestelagu.site/static/js/sw.js')
  .then(function(registration) {
    const subscribeOptions = {
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(applicationServerPublicKey)
    };

    return registration.pushManager.subscribe(subscribeOptions);
  })
  .then(function(pushSubscription) {
    console.log('Received PushSubscription: ', JSON.stringify(pushSubscription));

    sendSubscriptionToBackEnd(pushSubscription);
    return pushSubscription;
  });
}

function sendSubscriptionToBackEnd(subscription) {
  return fetch('/api/subscribe', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(subscription)
  })
  .then(function(response) {
    if (!response.ok) {
      throw new Error('Bad status code from server.1');
    }

    return response.json();
  })
  .then(function(responseData) {
    if (!(responseData.data && responseData.data.success)) {
      throw new Error('Bad response from server.2');
    }
  });
}

if ('serviceWorker' in navigator && 'PushManager' in window) {
    console.log('Service Worker and Push is supported');


    Notification.requestPermission().then(function (result) {
        if (result === 'denied') {
            console.log('Permission wasn\'t granted. Allow a retry.');
            return;
        }
        if (result === 'default') {
            console.log('The permission request was dismissed.');
            return;
        }
        // Do something with the granted permission.
        registerServiceWorker();
        pushSubscription = subscribeUserToPush();


    });
}