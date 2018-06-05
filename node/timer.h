// Simple software timer class.
class Timer
{
public:
  void (*Callback_Start)();
  void (*Callback_Tick)();
  void (*Callback_Stop)();

public:
  Timer() :
    Callback_Start( nullptr ),
    Callback_Tick( nullptr ),
    Callback_Stop( nullptr ),
    mStartTime( 0 ),
    mInterval( -1 ),
    mLooping( false )
  {}

  /** @param interval Time in ms. */
  void Start( int interval, bool looping )
  {
    if( interval >= 0 )
    {
      mInterval = interval;
      mLooping = looping;
      mStartTime = millis();
    
      if( Callback_Start ) Callback_Start();
    }
  }
  
  void Update()
  {
    if( IsActive() )
    {
      unsigned long now = millis();
      if( now - mStartTime > mInterval )
      {
        if( Callback_Tick ) Callback_Tick();
        
        if( !mLooping )
          Stop();
        else
          mStartTime = now;
      }
    }
  }

  void Stop()
  {
    if( IsActive() )
    {
      mInterval = -1;

      if( Callback_Stop ) Callback_Stop();
    }
  }

  inline bool IsActive() const
  {
    return mInterval >= 0;
  }
  
private:
  unsigned long mStartTime;
  int mInterval;
  bool mLooping;
};
