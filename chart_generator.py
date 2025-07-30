import matplotlib.pyplot as plt
import io

class ChartGenerator:
    """Chart generation class for spending summaries"""
    
    def __init__(self):
        # Beautiful colors with gradients
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                      '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
    
    def create_spending_chart(self, categories: list, amounts: list, currency: str, period_title: str):
        """Create a pie chart for spending summary"""
        # Set dark theme
        plt.style.use('dark_background')
        
        # Create the chart with enhanced styling - bigger size
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Custom autopct function to show both percentage and amount
        def make_autopct(values):
            def my_autopct(pct):
                total = sum(values)
                val = int(round(pct*total/100.0))
                return f'{pct:.1f}%\n({val:.0f})'
            return my_autopct
        
        # Create pie chart with enhanced styling
        wedges, texts, autotexts = ax.pie(
            amounts, 
            labels=categories, 
            autopct=make_autopct(amounts),
            startangle=90,
            colors=self.colors[:len(amounts)],
            explode=[0.05] * len(amounts),  # Slight separation between slices
            textprops={'fontsize': 12, 'color': 'white', 'weight': 'bold'},
            wedgeprops={'edgecolor': 'white', 'linewidth': 2}
        )
        
        # Enhance autopct text styling
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(11)
            autotext.set_weight('bold')
        
        # Add title with enhanced styling - centered at top
        plt.suptitle(
            f'Spending by Category - {period_title} ({currency})', 
            fontsize=24, 
            fontweight='bold', 
            color='white',
            y=0.85
        )
        
        # Add total amount as subtitle at bottom
        plt.figtext(
            0.5, 0.06, 
            f'Total Spent: {sum(amounts):.2f} {currency}', 
            ha='center', 
            fontsize=16, 
            fontweight='bold',
            color='#FFD700'  # Gold color for total
        )
        
        # Set background to black
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        
        # Center the pie chart with better margins and more free space
        ax.set_position([0.1, 0.15, 0.8, 0.65])  # [left, bottom, width, height]
        
        # Save the chart to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(
            buf, 
            format='png', 
            bbox_inches='tight', 
            dpi=150,
            facecolor='black',
            edgecolor='none',
            transparent=False
        )
        buf.seek(0)
        plt.close()
        
        return buf 